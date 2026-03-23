# pg 日志文件损坏，只有重建
`PostgreSQL 数据库的 WAL（Write-Ahead Logging）日志损坏，导致无法找到有效的 checkpoint 记录，从而无法启动。`

```shell
# 停止服务
cd ~/dify/docker
docker compose down

# 删除 PostgreSQL 数据目录（⚠️ 这会清空所有 Dify 数据！）
sudo rm -rf ./volumes/db

# 重建目录，分配权限
mkdir -p ./volumes/db
sudo chown -R 999:999 ./volumes/db

# 启动
docker compose up -d

# 验证
docker compose ps
```


# 启动日志
```shell
docker compose up -d
[+] Running 13/13
 ✔ Network docker_ssrf_proxy_network  Created                                                          0.0s 
 ✔ Network docker_default             Created                                                          0.0s 
 ✔ Container docker-ssrf_proxy-1      Started                                                          0.1s 
 ✘ Container docker-db-1              Error                                                            0.1s 
 ✔ Container docker-weaviate-1        Started                                                          0.1s 
 ✔ Container docker-sandbox-1         Started                                                          0.1s 
 ✔ Container docker-web-1             Started                                                          0.1s 
 ✔ Container docker-redis-1           Started                                                          0.1s 
 ✔ Container docker-plugin_daemon-1   Created                                                          0.0s 
 ✔ Container docker-api-1             Created                                                          0.0s 
 ✔ Container docker-worker-1          Created                                                          0.0s 
 ✔ Container docker-worker_beat-1     Created                                                          0.0s 
 ✔ Container docker-nginx-1           Created                                                          0.0s 
dependency failed to start: container docker-db-1 is unhealthy
```


# 容器日志
```shell
ocker logs docker-db-1

PostgreSQL Database directory appears to contain a database; Skipping initialization

2026-03-23 02:08:49.118 UTC [1] LOG:  starting PostgreSQL 15.14 on x86_64-pc-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit
2026-03-23 02:08:49.118 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
2026-03-23 02:08:49.118 UTC [1] LOG:  listening on IPv6 address "::", port 5432
2026-03-23 02:08:49.122 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-03-23 02:08:49.126 UTC [29] LOG:  database system shutdown was interrupted; last known up at 2026-02-13 13:18:46 UTC
2026-03-23 02:08:49.950 UTC [36] FATAL:  the database system is starting up
2026-03-23 02:08:50.155 UTC [29] LOG:  invalid resource manager ID in primary checkpoint record
2026-03-23 02:08:50.155 UTC [29] PANIC:  could not locate a valid checkpoint record
2026-03-23 02:08:50.222 UTC [1] LOG:  startup process (PID 29) was terminated by signal 6: Aborted
2026-03-23 02:08:50.222 UTC [1] LOG:  aborting startup due to startup process failure
2026-03-23 02:08:50.222 UTC [1] LOG:  database system is shut down

PostgreSQL Database directory appears to contain a database; Skipping initialization

2026-03-23 02:08:50.486 UTC [1] LOG:  starting PostgreSQL 15.14 on x86_64-pc-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit
2026-03-23 02:08:50.486 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
2026-03-23 02:08:50.486 UTC [1] LOG:  listening on IPv6 address "::", port 5432
2026-03-23 02:08:50.488 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-03-23 02:08:50.491 UTC [29] LOG:  database system shutdown was interrupted; last known up at 2026-02-13 13:18:46 UTC
2026-03-23 02:08:51.481 UTC [29] LOG:  invalid resource manager ID in primary checkpoint record
2026-03-23 02:08:51.481 UTC [29] PANIC:  could not locate a valid checkpoint record
2026-03-23 02:08:51.499 UTC [36] FATAL:  the database system is starting up
2026-03-23 02:08:51.542 UTC [1] LOG:  startup process (PID 29) was terminated by signal 6: Aborted
2026-03-23 02:08:51.542 UTC [1] LOG:  aborting startup due to startup process failure
2026-03-23 02:08:51.542 UTC [1] LOG:  database system is shut down

PostgreSQL Database directory appears to contain a database; Skipping initialization

2026-03-23 02:08:51.879 UTC [1] LOG:  starting PostgreSQL 15.14 on x86_64-pc-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit
2026-03-23 02:08:51.879 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
2026-03-23 02:08:51.879 UTC [1] LOG:  listening on IPv6 address "::", port 5432
2026-03-23 02:08:51.881 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-03-23 02:08:51.883 UTC [29] LOG:  database system shutdown was interrupted; last known up at 2026-02-13 13:18:46 UTC
2026-03-23 02:08:52.847 UTC [29] LOG:  invalid resource manager ID in primary checkpoint record
2026-03-23 02:08:52.847 UTC [29] PANIC:  could not locate a valid checkpoint record
2026-03-23 02:08:52.897 UTC [36] FATAL:  the database system is starting up
2026-03-23 02:08:52.910 UTC [1] LOG:  startup process (PID 29) was terminated by signal 6: Aborted
2026-03-23 02:08:52.910 UTC [1] LOG:  aborting startup due to startup process failure
2026-03-23 02:08:52.910 UTC [1] LOG:  database system is shut down

PostgreSQL Database directory appears to contain a database; Skipping initialization

2026-03-23 02:08:53.447 UTC [1] LOG:  starting PostgreSQL 15.14 on x86_64-pc-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit
2026-03-23 02:08:53.447 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
2026-03-23 02:08:53.447 UTC [1] LOG:  listening on IPv6 address "::", port 5432
2026-03-23 02:08:53.448 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-03-23 02:08:53.451 UTC [29] LOG:  database system shutdown was interrupted; last known up at 2026-02-13 13:18:46 UTC
2026-03-23 02:08:54.410 UTC [29] LOG:  invalid resource manager ID in primary checkpoint record
2026-03-23 02:08:54.410 UTC [29] PANIC:  could not locate a valid checkpoint record
2026-03-23 02:08:54.468 UTC [36] FATAL:  the database system is starting up
2026-03-23 02:08:54.473 UTC [1] LOG:  startup process (PID 29) was terminated by signal 6: Aborted
2026-03-23 02:08:54.473 UTC [1] LOG:  aborting startup due to startup process failure
2026-03-23 02:08:54.473 UTC [1] LOG:  database system is shut down

PostgreSQL Database directory appears to contain a database; Skipping initialization

2026-03-23 02:08:55.414 UTC [1] LOG:  starting PostgreSQL 15.14 on x86_64-pc-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit
2026-03-23 02:08:55.414 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
2026-03-23 02:08:55.414 UTC [1] LOG:  listening on IPv6 address "::", port 5432
2026-03-23 02:08:55.416 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-03-23 02:08:55.418 UTC [29] LOG:  database system shutdown was interrupted; last known up at 2026-02-13 13:18:46 UTC
2026-03-23 02:08:56.420 UTC [36] FATAL:  the database system is starting up
2026-03-23 02:08:56.433 UTC [29] LOG:  invalid resource manager ID in primary checkpoint record
2026-03-23 02:08:56.433 UTC [29] PANIC:  could not locate a valid checkpoint record
2026-03-23 02:08:56.496 UTC [1] LOG:  startup process (PID 29) was terminated by signal 6: Aborted
2026-03-23 02:08:56.496 UTC [1] LOG:  aborting startup due to startup process failure
2026-03-23 02:08:56.497 UTC [1] LOG:  database system is shut down

PostgreSQL Database directory appears to contain a database; Skipping initialization

2026-03-23 02:08:58.232 UTC [1] LOG:  starting PostgreSQL 15.14 on x86_64-pc-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit
2026-03-23 02:08:58.232 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
2026-03-23 02:08:58.232 UTC [1] LOG:  listening on IPv6 address "::", port 5432
2026-03-23 02:08:58.234 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-03-23 02:08:58.237 UTC [29] LOG:  database system shutdown was interrupted; last known up at 2026-02-13 13:18:46 UTC
2026-03-23 02:08:59.239 UTC [36] FATAL:  the database system is starting up
2026-03-23 02:08:59.588 UTC [29] LOG:  invalid resource manager ID in primary checkpoint record
2026-03-23 02:08:59.588 UTC [29] PANIC:  could not locate a valid checkpoint record
2026-03-23 02:08:59.648 UTC [1] LOG:  startup process (PID 29) was terminated by signal 6: Aborted
2026-03-23 02:08:59.648 UTC [1] LOG:  aborting startup due to startup process failure
2026-03-23 02:08:59.649 UTC [1] LOG:  database system is shut down

PostgreSQL Database directory appears to contain a database; Skipping initialization

2026-03-23 02:09:03.000 UTC [1] LOG:  starting PostgreSQL 15.14 on x86_64-pc-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit
2026-03-23 02:09:03.000 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
2026-03-23 02:09:03.000 UTC [1] LOG:  listening on IPv6 address "::", port 5432
2026-03-23 02:09:03.002 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-03-23 02:09:03.005 UTC [29] LOG:  database system shutdown was interrupted; last known up at 2026-02-13 13:18:46 UTC
2026-03-23 02:09:04.012 UTC [36] FATAL:  the database system is starting up
2026-03-23 02:09:04.251 UTC [29] LOG:  invalid resource manager ID in primary checkpoint record
2026-03-23 02:09:04.251 UTC [29] PANIC:  could not locate a valid checkpoint record
2026-03-23 02:09:04.312 UTC [1] LOG:  startup process (PID 29) was terminated by signal 6: Aborted
2026-03-23 02:09:04.312 UTC [1] LOG:  aborting startup due to startup process failure
2026-03-23 02:09:04.312 UTC [1] LOG:  database system is shut down

PostgreSQL Database directory appears to contain a database; Skipping initialization

2026-03-23 02:09:10.866 UTC [1] LOG:  starting PostgreSQL 15.14 on x86_64-pc-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit
2026-03-23 02:09:10.866 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
2026-03-23 02:09:10.866 UTC [1] LOG:  listening on IPv6 address "::", port 5432
2026-03-23 02:09:10.868 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-03-23 02:09:10.870 UTC [29] LOG:  database system shutdown was interrupted; last known up at 2026-02-13 13:18:46 UTC
2026-03-23 02:09:11.880 UTC [36] FATAL:  the database system is starting up
2026-03-23 02:09:11.886 UTC [29] LOG:  invalid resource manager ID in primary checkpoint record
2026-03-23 02:09:11.886 UTC [29] PANIC:  could not locate a valid checkpoint record
2026-03-23 02:09:11.946 UTC [1] LOG:  startup process (PID 29) was terminated by signal 6: Aborted
2026-03-23 02:09:11.946 UTC [1] LOG:  aborting startup due to startup process failure
2026-03-23 02:09:11.946 UTC [1] LOG:  database system is shut down

PostgreSQL Database directory appears to contain a database; Skipping initialization

2026-03-23 02:09:24.890 UTC [1] LOG:  starting PostgreSQL 15.14 on x86_64-pc-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit
2026-03-23 02:09:24.890 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
2026-03-23 02:09:24.890 UTC [1] LOG:  listening on IPv6 address "::", port 5432
2026-03-23 02:09:24.892 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-03-23 02:09:24.894 UTC [29] LOG:  database system shutdown was interrupted; last known up at 2026-02-13 13:18:46 UTC
2026-03-23 02:09:25.636 UTC [29] LOG:  invalid resource manager ID in primary checkpoint record
2026-03-23 02:09:25.636 UTC [29] PANIC:  could not locate a valid checkpoint record
2026-03-23 02:09:25.691 UTC [1] LOG:  startup process (PID 29) was terminated by signal 6: Aborted
2026-03-23 02:09:25.691 UTC [1] LOG:  aborting startup due to startup process failure
2026-03-23 02:09:25.692 UTC [1] LOG:  database system is shut down

PostgreSQL Database directory appears to contain a database; Skipping initialization

2026-03-23 02:09:51.435 UTC [1] LOG:  starting PostgreSQL 15.14 on x86_64-pc-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit
2026-03-23 02:09:51.435 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
2026-03-23 02:09:51.435 UTC [1] LOG:  listening on IPv6 address "::", port 5432
2026-03-23 02:09:51.437 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
2026-03-23 02:09:51.439 UTC [29] LOG:  database system shutdown was interrupted; last known up at 2026-02-13 13:18:46 UTC
2026-03-23 02:09:52.190 UTC [29] LOG:  invalid resource manager ID in primary checkpoint record
2026-03-23 02:09:52.190 UTC [29] PANIC:  could not locate a valid checkpoint record
2026-03-23 02:09:52.246 UTC [1] LOG:  startup process (PID 29) was terminated by signal 6: Aborted
2026-03-23 02:09:52.246 UTC [1] LOG:  aborting startup due to startup process failure
2026-03-23 02:09:52.246 UTC [1] LOG:  database system is shut down
```