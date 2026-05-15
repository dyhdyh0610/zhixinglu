import os
import uvicorn

if __name__ == "__main__":
    # 清理代理环境变量，避免 akshare 被代理阻断（uvicorn reload 时子进程可能继承代理）
    for var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
        os.environ.pop(var, None)
    os.environ["no_proxy"] = "*"
    uvicorn.run("app.main:app", host="0.0.0.0", port=5001, reload=True)
