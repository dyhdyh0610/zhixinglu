import os
import sys

# Force unset all proxy variables
for key in list(os.environ.keys()):
    if 'proxy' in key.lower() or 'PROXY' in key:
        del os.environ[key]

# Also set no_proxy to bypass any system proxy
os.environ['no_proxy'] = '*'
os.environ['NO_PROXY'] = '*'

print("Proxy env cleared, starting server...", file=sys.stderr)

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=5001, reload=False)
