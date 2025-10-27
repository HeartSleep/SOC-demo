// MongoDB initialization script
db = db.getSiblingDB('soc_platform');

// Create application user
db.createUser({
  user: 'soc_user',
  pwd: 'soc_password',
  roles: [
    {
      role: 'readWrite',
      db: 'soc_platform'
    }
  ]
});

// Create collections with indexes
db.createCollection('users');
db.users.createIndex({ username: 1 }, { unique: true });
db.users.createIndex({ email: 1 }, { unique: true });

db.createCollection('assets');
db.assets.createIndex({ name: 1, asset_type: 1 }, { unique: true });
db.assets.createIndex({ domain: 1 });
db.assets.createIndex({ ip_address: 1 });
db.assets.createIndex({ organization: 1 });
db.assets.createIndex({ tags: 1 });

db.createCollection('scan_tasks');
db.scan_tasks.createIndex({ task_type: 1 });
db.scan_tasks.createIndex({ status: 1 });
db.scan_tasks.createIndex({ created_by: 1 });
db.scan_tasks.createIndex({ created_at: -1 });

db.createCollection('vulnerabilities');
db.vulnerabilities.createIndex({ target_asset_id: 1 });
db.vulnerabilities.createIndex({ vulnerability_type: 1 });
db.vulnerabilities.createIndex({ severity: 1 });
db.vulnerabilities.createIndex({ status: 1 });
db.vulnerabilities.createIndex({ discovery_date: -1 });

db.createCollection('reports');
db.reports.createIndex({ report_type: 1 });
db.reports.createIndex({ created_by: 1 });
db.reports.createIndex({ created_at: -1 });

print('Database initialized successfully');