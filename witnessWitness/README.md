# Witness Witness

This is a proof of concept for creating a tracker history of Congressional hearing witnesses.

## Run the explorer locally

1. From the repository root start a static server. Any option works; for example:
   - Python: `python3 -m http.server 8000 --directory witnessWitness`
   - uv: `uv run python -m http.server 8000 --directory witnessWitness`
   - npm http-server: `npx http-server witnessWitness` (after `npm init -y` and `npm install --save-dev http-server`)
2. Open your browser to `http://localhost:8000/` (or the port shown in the server output).
3. Interact with `index.html` to explore witnesses, filter hearings, and follow hearing links.
