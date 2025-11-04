"""
Simple in-memory database for local development
替代MongoDB的内存数据库实现
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading
import time


class SimpleDB:
    """简单的内存数据库"""
    
    def __init__(self):
        self.data: Dict[str, List[Dict]] = {
            'users': [],
            'assets': [],
            'tasks': [],
            'vulnerabilities': [],
            'reports': []
        }
        self.data_file = 'soc_local_data.json'
        self._dirty = False
        self._save_lock = threading.Lock()
        self.load_data()
        self._init_default_data()
        # Start background save thread
        self._start_auto_save()
    
    def load_data(self):
        """从文件加载数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except:
                pass
    
    def _start_auto_save(self):
        """启动后台自动保存线程"""
        def auto_save_worker():
            while True:
                time.sleep(5)  # 每5秒检查一次
                if self._dirty:
                    self._save_data()

        thread = threading.Thread(target=auto_save_worker, daemon=True)
        thread.start()

    def _mark_dirty(self):
        """标记数据已修改"""
        self._dirty = True

    def save_data(self):
        """立即保存数据到文件"""
        self._save_data()

    def _save_data(self):
        """内部保存方法"""
        with self._save_lock:
            try:
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2, default=str)
                self._dirty = False
            except Exception as e:
                print(f"保存数据失败: {e}")
    
    def _init_default_data(self):
        """初始化默认数据"""
        if not self.data.get('users'):
            # 创建默认管理员用户
            self.data['users'] = [{
                'id': '1',
                'username': 'admin',
                'email': 'admin@soc.com',
                'full_name': '系统管理员',
                'hashed_password': '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',  # admin123
                'role': 'admin',
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'permissions': ['all']
            }]
        
        if not self.data.get('assets'):
            # 创建示例资产
            self.data['assets'] = [
                {
                    'id': '1',
                    'name': 'example.com',
                    'type': 'domain',
                    'target': 'example.com',
                    'description': '示例域名资产',
                    'status': 'active',
                    'created_at': datetime.now().isoformat(),
                    'tags': ['web', 'domain']
                },
                {
                    'id': '2', 
                    'name': '192.168.1.1',
                    'type': 'ip',
                    'target': '192.168.1.1',
                    'description': '示例IP资产',
                    'status': 'active',
                    'created_at': datetime.now().isoformat(),
                    'tags': ['network', 'ip']
                }
            ]
        
        self.save_data()
    
    def find(self, collection: str, query: Dict = None) -> List[Dict]:
        """查找数据"""
        items = self.data.get(collection, [])
        if not query:
            return items
        
        result = []
        for item in items:
            match = True
            for key, value in query.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                result.append(item)
        return result
    
    def find_one(self, collection: str, query: Dict) -> Optional[Dict]:
        """查找单个数据"""
        results = self.find(collection, query)
        return results[0] if results else None
    
    def insert(self, collection: str, data: Dict) -> Dict:
        """插入数据"""
        if collection not in self.data:
            self.data[collection] = []
        
        # 自动生成ID
        if 'id' not in data:
            max_id = 0
            for item in self.data[collection]:
                if 'id' in item:
                    try:
                        max_id = max(max_id, int(item['id']))
                    except:
                        pass
            data['id'] = str(max_id + 1)
        
        # 添加创建时间
        if 'created_at' not in data:
            data['created_at'] = datetime.now().isoformat()
        
        self.data[collection].append(data)
        self._mark_dirty()
        return data
    
    def update(self, collection: str, query: Dict, update_data: Dict) -> bool:
        """更新数据"""
        items = self.data.get(collection, [])
        updated = False
        
        for item in items:
            match = True
            for key, value in query.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            
            if match:
                item.update(update_data)
                item['updated_at'] = datetime.now().isoformat()
                updated = True
        
        if updated:
            self._mark_dirty()
        return updated
    
    def delete(self, collection: str, query: Dict) -> bool:
        """删除数据"""
        items = self.data.get(collection, [])
        original_length = len(items)
        
        self.data[collection] = [
            item for item in items
            if not all(
                key in item and item[key] == value
                for key, value in query.items()
            )
        ]
        
        deleted = len(self.data[collection]) < original_length
        if deleted:
            self._mark_dirty()
        return deleted


# 全局数据库实例
simple_db = SimpleDB()


async def init_database():
    """初始化数据库连接"""
    print("使用简化内存数据库 (本地开发模式)")
    return True


async def close_database():
    """关闭数据库连接"""
    simple_db.save_data()


def is_database_connected() -> bool:
    """检查数据库连接状态"""
    return True


def get_database():
    """获取数据库实例"""
    return simple_db
