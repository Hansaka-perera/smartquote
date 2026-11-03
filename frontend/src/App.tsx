import { NavLink, Route, Routes } from "react-router-dom";
import { useState } from "react";
import { Toasts } from "./components/ui";
import Dashboard from "./pages/Dashboard";
import NewQuotation from "./pages/NewQuotation";
import AluminiumDesigner from "./pages/AluminiumDesigner";
import BoardDesigner from "./pages/BoardDesigner";
import Products from "./pages/Products";
import Materials from "./pages/Materials";
import MaterialPrices from "./pages/MaterialPrices";
import Customers from "./pages/Customers";
import { QuotationList, QuotationDetail } from "./pages/Quotations";
import Settings from "./pages/Settings";

const NAV: [string, string][] = [
  ["/", "Dashboard"], ["/quotations/new", "New Quotation"], ["/aluminium", "Aluminium Designer"],
  ["/board", "Board Furniture Designer"], ["/products", "Products"], ["/materials", "Materials"],
  ["/prices", "Material Prices"], ["/customers", "Customers"], ["/quotations", "Quotations"], ["/settings", "Settings"],
];

export default function App() {
  const [dark, setDark] = useState(document.documentElement.classList.contains("dark"));
  const toggle = () => {
    document.documentElement.classList.toggle("dark");
    const d = document.documentElement.classList.contains("dark");
    localStorage.setItem("sq-theme", d ? "dark" : "light");
    setDark(d);
  };
  return (
    <div className="flex h-full">
      <nav className="flex w-56 shrink-0 flex-col border-r border-line bg-panel print:hidden" aria-label="Main">
        <div className="border-b border-line px-4 py-4">
          <div className="text-[17px] font-semibold tracking-tight">SmartQuote Studio</div>
          <div className="text-[12px] text-mute">Aluminium and board quotations</div>
        </div>
        <ul className="flex-1 overflow-auto py-2">
          {NAV.map(([to, label]) => (
            <li key={to}>
              <NavLink to={to} end={to === "/" || to === "/quotations"}
                className={({ isActive }) => `block border-l-2 px-4 py-2 ${isActive ? "border-accent bg-sunk font-semibold text-accent" : "border-transparent text-ink hover:bg-sunk"}`}>
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
        <button className="btn m-3" onClick={toggle}>{dark ? "Light theme" : "Dark theme"}</button>
      </nav>
      <main className="min-w-0 flex-1 overflow-auto p-5">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/quotations/new" element={<NewQuotation />} />
          <Route path="/aluminium" element={<AluminiumDesigner />} />
          <Route path="/board" element={<BoardDesigner />} />
          <Route path="/products" element={<Products />} />
          <Route path="/materials" element={<Materials />} />
          <Route path="/prices" element={<MaterialPrices />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/quotations" element={<QuotationList />} />
          <Route path="/quotations/:id" element={<QuotationDetail />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
      <Toasts />
    </div>
  );
}
