#!/bin/bash
# 从国内镜像源拉取Docker基础镜像

echo "========================================="
echo "  从国内镜像源拉取Docker基础镜像"
echo "========================================="
echo ""

# 定义镜像列表
images=(
    "python:3.12-slim"
    "node:18-alpine"
    "nginx:alpine"
)

# 国内镜像源列表
mirrors=(
    "docker.m.daocloud.io"
    "docker.1panel.live"
    "docker.anyhub.us.kg"
    "dockerhub.icu"
)

success_count=0
total_count=${#images[@]}

for image in "${images[@]}"; do
    echo "----------------------------------------"
    echo "拉取镜像: $image"
    echo "----------------------------------------"

    pulled=false

    for mirror in "${mirrors[@]}"; do
        if [ "$pulled" = true ]; then
            break
        fi

        echo "尝试镜像源: $mirror"

        # 尝试从当前镜像源拉取
        if docker pull "$mirror/$image"; then
            # 重新标记为原始名称
            docker tag "$mirror/$image" "$image"
            echo "✓ 成功从 $mirror 拉取 $image"
            success_count=$((success_count + 1))
            pulled=true
            break
        else
            echo "✗ 从 $mirror 拉取失败"
        fi
    done

    if [ "$pulled" = false ]; then
        echo "✗ 无法从任何镜像源拉取 $image"
    fi

    echo ""
done

echo "========================================="
echo "拉取完成!"
echo "成功: $success_count / $total_count"
echo "========================================="
echo ""

# 显示本地镜像
echo "本地Docker镜像列表:"
docker images | grep -E "python|node|nginx"

echo ""
echo "镜像拉取完成后,可以运行部署命令:"
echo "  cd d:\\github\\QuantDinger"
echo "  docker compose up -d --build"
