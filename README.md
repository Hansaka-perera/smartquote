# SmartQuote Studio
Aluminium and board-furniture quotation system. Runs locally on Windows, no login, no paid services.

## Install (Windows)
1. Install **Python 3.10+** (python.org – tick *Add python.exe to PATH*). Node.js 18+ is optional: the interface is pre-built in `frontend\dist`; install Node only if you want to modify the UI.
2. Double-click **setup.bat** (creates a virtual environment, installs packages, loads SAMPLE materials).
3. Double-click **start.bat**. The browser opens at http://localhost:8000.

Your data lives in `data\smartquote.db` (SQLite). Back it up by copying that file.
Run **test.bat** to execute the automated tests. **dev.bat** starts hot-reload development mode (needs Node).

## First steps
1. *Materials / Material Prices*: the sample prices (LKR) are for testing only – replace them with your real supplier prices.
2. *Settings*: company details and logo, tax, currency, kerf, default labour/overhead/profit, terms.
3. *Settings → Aluminium systems*: the shipped cutting formulas are generic. Edit the deductions/formulas to match your extrusion supplier's system.
4. *New Quotation* → create it → open *Aluminium Designer* or *Board Furniture Designer* → **Add to quotation** → open the quotation → preview/download/print PDF or export Excel.

## How the pieces connect
* The designer's width/height/panels (or furniture overall size + components) are sent to the calculation engine – nothing is hardcoded.
* Engine → cut list → bar/sheet optimiser → material quantities × saved prices → cost summary (labour, overhead, profit).
* **Add to quotation** freezes the engine output and the prices used (`quotation_items.calc`, `price_snapshot`, `cost_breakdowns`). Changing a material price later does **not** change existing quotations. Use *Re-price* on an item to refresh it deliberately; *Duplicate* copies frozen prices.
* The PDF shows quantities only (no internal cost or profit).

## Costing modes (Settings → General)
* Aluminium: *length consumed (+ wastage %)* or *full bars for the batch*.
* Boards: *practical sheets from the cutting layout* or *board area (+ wastage %)*. The Sheets tab shows theoretical vs practical sheet counts side by side.

## Architecture
`backend/app/engines` pure calculation code (safe formula evaluator, units, cutting optimisers, aluminium, board, costing) · `services` DB glue, PDF, Excel · `routers` REST API · `frontend/src` React + TypeScript + Tailwind.
Switching to PostgreSQL later: set `DATABASE_URL` (models use portable types).

## Known limitations (honest status)
* Drawing canvas is custom SVG (not Fabric/Konva): zoom, pan, grid, snap, resize handles, panel selection, undo/redo, templates. Panels are equal width; free-form dragging of mullions and arbitrary shapes is not implemented yet.
* Schema is created with `create_all`; Alembic migrations are not set up yet – add them before changing models in production.
* Sheet layout uses a shelf-based heuristic (good, not guaranteed optimal). Furniture PDF drawing is a simple front outline.
* Default aluminium formulas/prices are placeholders, not a real manufacturer's data.
