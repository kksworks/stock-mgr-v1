import logging
from flask import Blueprint, request, jsonify, session
from bson.objectid import ObjectId
from datetime import datetime, timezone
from backend.services import board_collection
from backend.routes.auth_api import login_required, admin_required

bp = Blueprint('board_api', __name__)

def _serialize_post(post):
    """MongoDB 문서를 JSON 직렬화 가능한 형식으로 변환"""
    if not post:
        return None
    post['id'] = str(post.pop('_id'))
    return post

@bp.route('/board/posts', methods=['GET'])
def list_posts():
    """게시물 목록 조회 (페이징 지원, 고정글 우선)"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        skip = (page - 1) * per_page
        
        # 고정글(pinned) 내림차순, 작성일(created_at) 내림차순
        cursor = board_collection.find().sort([("pinned", -1), ("created_at", -1)]).skip(skip).limit(per_page)
        
        posts = [_serialize_post(p) for p in cursor]
        total_count = board_collection.count_documents({})
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            'posts': posts,
            'page': page,
            'total_pages': total_pages,
            'total_count': total_count
        })
    except Exception as e:
        logging.error("Failed to list board posts: %s", str(e))
        return jsonify({'error': '게시물을 불러오는데 실패했습니다.'}), 500

@bp.route('/board/posts/<post_id>', methods=['GET'])
def get_post(post_id):
    """단일 게시물 상세 조회"""
    try:
        post = board_collection.find_one({'_id': ObjectId(post_id)})
        if not post:
            return jsonify({'error': '게시물을 찾을 수 없습니다.'}), 404
            
        return jsonify(_serialize_post(post))
    except Exception as e:
        logging.error("Failed to get board post %s: %s", post_id, str(e))
        return jsonify({'error': '게시물을 불러오는데 실패했습니다.'}), 500

@bp.route('/board/posts', methods=['POST'])
@admin_required
def create_post():
    """새 게시물 작성 (관리자 전용)"""
    try:
        data = request.json
        title = data.get('title')
        content = data.get('content')
        pinned = data.get('pinned', False)
        
        if not title or not content:
            return jsonify({'error': '제목과 내용을 입력해주세요.'}), 400
            
        new_post = {
            'title': title,
            'content': content,
            'pinned': pinned,
            'author_id': session.get('user_id'),
            'author_name': session.get('username'),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = board_collection.insert_one(new_post)
        new_post['id'] = str(result.inserted_id)
        new_post.pop('_id', None)
        
        return jsonify(new_post), 201
    except Exception as e:
        logging.error("Failed to create board post: %s", str(e))
        return jsonify({'error': '게시물 작성에 실패했습니다.'}), 500

@bp.route('/board/posts/<post_id>', methods=['PUT'])
@admin_required
def update_post(post_id):
    """게시물 수정 (관리자 전용)"""
    try:
        data = request.json
        title = data.get('title')
        content = data.get('content')
        pinned = data.get('pinned')
        
        update_data = {
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        if title is not None: update_data['title'] = title
        if content is not None: update_data['content'] = content
        if pinned is not None: update_data['pinned'] = pinned
        
        result = board_collection.update_one(
            {'_id': ObjectId(post_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': '게시물을 찾을 수 없습니다.'}), 404
            
        return jsonify({'success': True, 'message': '게시물이 수정되었습니다.'})
    except Exception as e:
        logging.error("Failed to update board post %s: %s", post_id, str(e))
        return jsonify({'error': '게시물 수정에 실패했습니다.'}), 500

@bp.route('/board/posts/<post_id>', methods=['DELETE'])
@admin_required
def delete_post(post_id):
    """게시물 삭제 (관리자 전용)"""
    try:
        result = board_collection.delete_one({'_id': ObjectId(post_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': '게시물을 찾을 수 없습니다.'}), 404
            
        return jsonify({'success': True, 'message': '게시물이 삭제되었습니다.'})
    except Exception as e:
        logging.error("Failed to delete board post %s: %s", post_id, str(e))
        return jsonify({'error': '게시물 삭제에 실패했습니다.'}), 500

@bp.route('/board/posts/<post_id>/toggle-pin', methods=['PUT'])
@admin_required
def toggle_pin(post_id):
    """게시물 상단 고정 토글 (관리자 전용)"""
    try:
        post = board_collection.find_one({'_id': ObjectId(post_id)})
        if not post:
            return jsonify({'error': '게시물을 찾을 수 없습니다.'}), 404
            
        new_pinned = not post.get('pinned', False)
        board_collection.update_one(
            {'_id': ObjectId(post_id)},
            {'$set': {'pinned': new_pinned, 'updated_at': datetime.now(timezone.utc).isoformat()}}
        )
        
        return jsonify({'success': True, 'pinned': new_pinned})
    except Exception as e:
        logging.error("Failed to toggle pin for post %s: %s", post_id, str(e))
        return jsonify({'error': '고정 상태 변경에 실패했습니다.'}), 500
