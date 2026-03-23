# 部署
## docker启动
```shell
# 下载
git clone --branch "$(curl -s https://api.github.com/repos/langgenius/dify/releases/latest | jq -r .tag_name)" https://github.com/langgenius/dify.git

# 
cd dify/docker
cp .env.example .env

# v2启动
docker compose up -d
# v1 docker-compose up -d

# 查看服务
docker compose ps
```

## 启动正常日志
```shell
NAME                     IMAGE                                       COMMAND                  SERVICE         CREATED          STATUS                             PORTS
docker-api-1             langgenius/dify-api:1.10.1                  "/bin/bash /entrypoi…"   api             26 seconds ago   Up 22 seconds                      5001/tcp
docker-db_postgres-1     postgres:15-alpine                          "docker-entrypoint.s…"   db_postgres     26 seconds ago   Up 25 seconds (healthy)            5432/tcp
docker-nginx-1           nginx:latest                                "sh -c 'cp /docker-e…"   nginx           26 seconds ago   Up 22 seconds                      0.0.0.0:80->80/tcp, :::80->80/tcp, 0.0.0.0:443->443/tcp, :::443->443/tcp
docker-plugin_daemon-1   langgenius/dify-plugin-daemon:0.4.1-local   "/bin/bash -c /app/e…"   plugin_daemon   26 seconds ago   Up 22 seconds                      0.0.0.0:5003->5003/tcp, :::5003->5003/tcp
docker-redis-1           redis:6-alpine                              "docker-entrypoint.s…"   redis           26 seconds ago   Up 25 seconds (health: starting)   6379/tcp
docker-sandbox-1         langgenius/dify-sandbox:0.2.12              "/main"                  sandbox         26 seconds ago   Up 25 seconds (health: starting)   
docker-ssrf_proxy-1      ubuntu/squid:latest                         "sh -c 'cp /docker-e…"   ssrf_proxy      26 seconds ago   Up 25 seconds                      3128/tcp
docker-weaviate-1        semitechnologies/weaviate:1.27.0            "/bin/weaviate --hos…"   weaviate        26 seconds ago   Up 25 seconds                      
docker-web-1             langgenius/dify-web:1.10.1                  "/bin/sh ./entrypoin…"   web             26 seconds ago   Up 25 seconds                      3000/tcp
docker-worker-1          langgenius/dify-api:1.10.1                  "/bin/bash /entrypoi…"   worker          26 seconds ago   Up 22 seconds                      5001/tcp
docker-worker_beat-1     langgenius/dify-api:1.10.1                  "/bin/bash /entrypoi…"   worker_beat     26 seconds ago   Up 22 seconds                      5001/tcp
```

## 访问
http://192.168.1.123/apps


# 基础业务配置

## 模型供应商
安装插件
配置api