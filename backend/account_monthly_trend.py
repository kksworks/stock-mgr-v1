"""
대시보드 스파크라인용 월별 수익금(investment_return) 스냅샷.
balance_history 일별 문서에서 월마다 마지막 일자 값 1건만 유지해 조회 비용을 고정한다.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from bson.decimal128 import Decimal128
from pymongo import UpdateOne
from pymongo.collection import Collection

from backend.time_utils import now_kst

logger = logging.getLogger(__name__)


def month_key_from_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str or len(date_str) < 7:
        return None
    return date_str[:7]


def _coerce_investment_return(raw: Any) -> int:
    if raw is None:
        return 0
    if isinstance(raw, Decimal128):
        try:
            return int(raw.to_decimal())
        except Exception:
            return 0
    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, int):
        return raw
    try:
        return int(raw)
    except (TypeError, ValueError):
        try:
            return int(float(raw))
        except (TypeError, ValueError):
            return 0


def upsert_monthly_trend_row(
    trend_col: Collection,
    account_id: Optional[str],
    date_str: str,
    investment_return: Any,
) -> None:
    """balance_history 저장 직후 호출: 해당 월의 대표값을 최신 일자 기준으로 갱신."""
    if not account_id or not date_str:
        return
    month = month_key_from_date(date_str)
    if not month:
        return
    ir = _coerce_investment_return(investment_return)
    existing = trend_col.find_one({'account_id': account_id, 'month': month}, {'source_date': 1})
    prev_sd = (existing or {}).get('source_date')
    if prev_sd is not None and str(prev_sd) > date_str:
        return
    trend_col.update_one(
        {'account_id': account_id, 'month': month},
        {
            '$set': {
                'account_id': account_id,
                'month': month,
                'investment_return': ir,
                'source_date': date_str,
                'updated_at': now_kst(),
            }
        },
        upsert=True,
    )


def monthly_cutoff_key(months_back: int = 12) -> str:
    """포함 시작 월(당월 포함 최대 months_back+1개 월 버킷)."""
    d = now_kst().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    d = d - pd.DateOffset(months=months_back)
    return d.strftime('%Y-%m')


def load_monthly_trend_series(
    trend_col: Collection,
    account_ids: List[str],
    min_month: str,
) -> Dict[str, List[Tuple[str, int]]]:
    """account_id -> [(month 'YYYY-MM', investment_return), ...] 월 오름차순.

    여러 계좌를 합산할 때는 동일 월끼리 더해야 하므로, 인덱스만으로 합산하면 안 된다.
    """
    if not account_ids:
        return {}
    out: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
    cur = trend_col.find(
        {'account_id': {'$in': list(account_ids)}, 'month': {'$gte': min_month}},
        {'_id': 0, 'account_id': 1, 'month': 1, 'investment_return': 1},
    ).sort([('account_id', 1), ('month', 1)])
    for doc in cur:
        aid = doc.get('account_id')
        if not aid:
            continue
        raw_m = doc.get('month')
        if raw_m is None:
            continue
        mstr = str(raw_m).strip()
        if len(mstr) >= 7:
            mstr = mstr[:7]
        else:
            continue
        out[aid].append((mstr, _coerce_investment_return(doc.get('investment_return'))))
    return dict(out)


def backfill_monthly_trends_from_history(
    balance_history_col: Collection,
    trend_col: Collection,
    account_ids: List[str],
    min_month: str,
) -> int:
    """
    월별 트렌드가 비어 있는 계좌에 대해 balance_history를 월 단위로 한 번 집계해 채운다.
    반환: upsert 시도 건수.
    """
    if not account_ids:
        return 0
    min_date = f'{min_month}-01'
    pipeline = [
        {'$match': {'account_id': {'$in': list(account_ids)}, 'date': {'$gte': min_date}}},
        {'$sort': {'date': 1}},
        {
            '$group': {
                '_id': {'a': '$account_id', 'm': {'$substr': ['$date', 0, 7]}},
                'investment_return': {'$last': '$investment_return'},
                'source_date': {'$last': '$date'},
            }
        },
    ]
    try:
        rows = list(balance_history_col.aggregate(pipeline, allowDiskUse=False))
    except Exception as e:
        logger.warning('monthly trend backfill aggregate failed: %s', e)
        return 0
    if not rows:
        return 0
    now = now_kst()
    ops: List[UpdateOne] = []
    for r in rows:
        key = r.get('_id') or {}
        aid = key.get('a')
        m = key.get('m')
        if not aid or not m or len(str(m)) != 7:
            continue
        sd = r.get('source_date')
        if sd is not None:
            sd = str(sd)[:10]
        ir = _coerce_investment_return(r.get('investment_return'))
        ops.append(
            UpdateOne(
                {'account_id': aid, 'month': m},
                {
                    '$set': {
                        'account_id': aid,
                        'month': m,
                        'investment_return': ir,
                        'source_date': sd,
                        'updated_at': now,
                    }
                },
                upsert=True,
            )
        )
    if not ops:
        return 0
    try:
        trend_col.bulk_write(ops, ordered=False)
    except Exception as e:
        logger.warning('monthly trend bulk_write failed: %s', e)
        return 0
    return len(ops)


def account_ids_needing_trend_backfill(
    trend_col: Collection,
    account_ids: List[str],
    min_month: str,
) -> List[str]:
    """구간 내 월별 문서가 하나도 없는 계좌만 (히스토리 임포트 직후 등)."""
    if not account_ids:
        return []
    have = {
        d['_id']
        for d in trend_col.aggregate(
            [
                {'$match': {'account_id': {'$in': list(account_ids)}, 'month': {'$gte': min_month}}},
                {'$group': {'_id': '$account_id'}},
            ],
            allowDiskUse=False,
        )
    }
    return [aid for aid in account_ids if aid not in have]
