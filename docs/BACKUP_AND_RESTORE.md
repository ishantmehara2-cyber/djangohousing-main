# Database Backup & Restore

## MySQL Backup
```bash
mysqldump -u root -p housing_clone_django > backup_$(date +%F).sql
```

## MySQL Restore
```bash
mysql -u root -p housing_clone_django < backup_YYYY-MM-DD.sql
```
