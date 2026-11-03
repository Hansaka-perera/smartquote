from datetime import datetime, date
from sqlalchemy import (String, Integer, Float, Boolean, Date, DateTime, ForeignKey, JSON, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

now = datetime.utcnow


class Supplier(Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(120))


class MaterialCategory(Base):
    __tablename__ = "material_categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)


class Material(Base):
    """One table for every material. Aluminium profiles use bar_length_mm /
    cutting_allowance_mm / profile_type / weight_per_m; boards use
    sheet_length_mm / sheet_width_mm / thickness_mm (these are the 'Aluminium
    profiles' and 'Board types' of the spec, filtered by category)."""
    __tablename__ = "materials"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    category_id: Mapped[int] = mapped_column(ForeignKey("material_categories.id"))
    unit: Mapped[str] = mapped_column(String(20))
    purchase_price: Mapped[float] = mapped_column(Float, default=0)
    selling_price: Mapped[float] = mapped_column(Float, default=0)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    wastage_pct: Mapped[float] = mapped_column(Float, default=0)
    min_stock: Mapped[float | None] = mapped_column(Float)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    profile_type: Mapped[str | None] = mapped_column(String(40))
    bar_length_mm: Mapped[float | None] = mapped_column(Float)
    cutting_allowance_mm: Mapped[float | None] = mapped_column(Float)
    weight_per_m: Mapped[float | None] = mapped_column(Float)
    sheet_length_mm: Mapped[float | None] = mapped_column(Float)
    sheet_width_mm: Mapped[float | None] = mapped_column(Float)
    thickness_mm: Mapped[float | None] = mapped_column(Float)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)
    category: Mapped[MaterialCategory] = relationship()
    supplier: Mapped[Supplier | None] = relationship()


class MaterialPrice(Base):
    __tablename__ = "material_prices"
    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="CASCADE"), index=True)
    purchase_price: Mapped[float] = mapped_column(Float)
    selling_price: Mapped[float] = mapped_column(Float)
    effective_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    note: Mapped[str | None] = mapped_column(String(200))


class AluminiumSystem(Base):
    __tablename__ = "aluminium_systems"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(20), default="window")
    config: Mapped[dict] = mapped_column(JSON)  # formulas - see engines/default_systems.py
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    company: Mapped[str | None] = mapped_column(String(160))
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(20))  # aluminium | board
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    designs: Mapped[list["ProductDesign"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class ProductDesign(Base):
    __tablename__ = "product_designs"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    system_code: Mapped[str | None] = mapped_column(String(40))
    params: Mapped[dict] = mapped_column(JSON)
    cost_cfg: Mapped[dict | None] = mapped_column(JSON)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)
    product: Mapped[Product] = relationship(back_populates="designs")
    components: Mapped[list["DesignComponent"]] = relationship(cascade="all, delete-orphan")


class DesignComponent(Base):
    __tablename__ = "design_components"
    id: Mapped[int] = mapped_column(primary_key=True)
    design_id: Mapped[int] = mapped_column(ForeignKey("product_designs.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    data: Mapped[dict] = mapped_column(JSON)


class Quotation(Base):
    __tablename__ = "quotations"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"))
    customer_name: Mapped[str] = mapped_column(String(120))
    company: Mapped[str | None] = mapped_column(String(160))
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(120))
    project_name: Mapped[str | None] = mapped_column(String(160))
    delivery_location: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    terms: Mapped[str | None] = mapped_column(Text)
    quote_date: Mapped[date] = mapped_column(Date, default=date.today)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="Draft", index=True)
    currency: Mapped[str] = mapped_column(String(8), default="LKR")
    discount_mode: Mapped[str] = mapped_column(String(10), default="percent")
    discount_value: Mapped[float] = mapped_column(Float, default=0)
    tax_percent: Mapped[float] = mapped_column(Float, default=0)
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0)
    total: Mapped[float] = mapped_column(Float, default=0)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)
    items: Mapped[list["QuotationItem"]] = relationship(back_populates="quotation", cascade="all, delete-orphan",
                                                        order_by="QuotationItem.position")
    versions: Mapped[list["QuotationVersion"]] = relationship(cascade="all, delete-orphan",
                                                              order_by="QuotationVersion.version_no")


class QuotationItem(Base):
    __tablename__ = "quotation_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_id: Mapped[int] = mapped_column(ForeignKey("quotations.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(20))
    system_code: Mapped[str | None] = mapped_column(String(40))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    params: Mapped[dict] = mapped_column(JSON)       # drawing / measurement source of the calculation
    cost_cfg: Mapped[dict] = mapped_column(JSON)
    calc: Mapped[dict] = mapped_column(JSON)         # engine output frozen at creation (price snapshot)
    price_snapshot: Mapped[dict] = mapped_column(JSON)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    total_price: Mapped[float] = mapped_column(Float, default=0)
    priced_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    quotation: Mapped[Quotation] = relationship(back_populates="items")
    breakdown: Mapped[list["CostBreakdown"]] = relationship(cascade="all, delete-orphan")
    cutting_lists: Mapped[list["CuttingList"]] = relationship(cascade="all, delete-orphan")


class CostBreakdown(Base):
    __tablename__ = "cost_breakdowns"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("quotation_items.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(30))
    code: Mapped[str | None] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(String(250))
    quantity: Mapped[float] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(20))
    unit_price: Mapped[float] = mapped_column(Float)
    amount: Mapped[float] = mapped_column(Float)


class CuttingList(Base):
    __tablename__ = "cutting_lists"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("quotation_items.id", ondelete="CASCADE"), index=True)
    material_code: Mapped[str] = mapped_column(String(40))
    data: Mapped[dict] = mapped_column(JSON)


class QuotationVersion(Base):
    __tablename__ = "quotation_versions"
    __table_args__ = (UniqueConstraint("quotation_id", "version_no"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_id: Mapped[int] = mapped_column(ForeignKey("quotations.id", ondelete="CASCADE"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(String(200))
    snapshot: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
