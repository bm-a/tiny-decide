# Self-hosting (Jev-compatible)

```bash
pip install tiny-decide
tiny-decide-serve --host 127.0.0.1 --port 8787
curl localhost:8787/health
curl localhost:8787/v1/systemone -H 'Content-Type: application/json' \
  -d '{"state":"please cancel my plan","questions":{"intent":{"type":"choice","options":["billing","cancel"]}}}'
```

Point any Jev client at `http://127.0.0.1:8787` as `baseUrl`. No key needed.
