"use client";

import React, { useState, useEffect } from "react";
import {
  Gem,
  Plus,
  Search,
  Upload,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Tag,
  Scale,
  ArrowRight,
  FileSpreadsheet,
} from "lucide-react";
import { ProductItem, CSVPreviewResult, CSVImportResult, api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

export default function CatalogueView() {
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  
  // CSV Import State
  const [isCsvOpen, setIsCsvOpen] = useState(false);
  const [csvStep, setCsvStep] = useState<"upload" | "map" | "result">("upload");
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<CSVPreviewResult | null>(null);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [importResult, setImportResult] = useState<CSVImportResult | null>(null);
  const [isProcessingCsv, setIsProcessingCsv] = useState(false);
  const [csvError, setCsvError] = useState<string | null>(null);

  // New product form
  const [formData, setFormData] = useState({
    sku: "",
    name: "",
    category: "Rings",
    price: "",
    gold_purity: "22K",
    gross_weight: "",
    stock: "1",
    description: "",
    image_url: "",
  });

  const loadProducts = async () => {
    try {
      setLoading(true);
      setError("");
      const res = await api.getProducts({
        category: selectedCategory,
        search: search.trim() || undefined,
      });
      setProducts(res.items);
      setCategories(["All", ...res.categories]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load the catalogue. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, [selectedCategory]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadProducts();
  };

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (saving) return;
    if (!formData.sku || !formData.name || !formData.price) {
      alert("Please fill in SKU, Name, and Price.");
      return;
    }
    try {
      setSaving(true);
      await api.createProduct({
        sku: formData.sku,
        name: formData.name,
        category: formData.category,
        price: parseFloat(formData.price),
        gold_purity: formData.gold_purity,
        gross_weight: formData.gross_weight ? parseFloat(formData.gross_weight) : undefined,
        stock: Number(formData.stock),
        description: formData.description,
        image_urls: formData.image_url ? [formData.image_url] : [],
      });
      setIsAddOpen(false);
      setFormData({
        sku: "",
        name: "",
        category: "Rings",
        price: "",
        gold_purity: "22K",
        gross_weight: "",
        stock: "1",
        description: "",
        image_url: "",
      });
      loadProducts();
    } catch (err: any) {
      alert("Error adding product: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this catalogue item?")) return;
    try {
      await api.deleteProduct(id);
      loadProducts();
    } catch (err) {
      alert("Failed to delete product: " + err);
    }
  };

  const handleCsvPreview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvFile) return;
    setIsProcessingCsv(true);
    setCsvError(null);

    try {
      const preview = await api.previewCsv(csvFile);
      setPreviewData(preview);
      // Initialize mappings from suggested mappings
      const initialMap: Record<string, string> = { ...preview.suggested_mappings };
      setColumnMapping(initialMap);
      setCsvStep("map");
    } catch (err: any) {
      setCsvError(err.message || "Failed to parse CSV preview");
    } finally {
      setIsProcessingCsv(false);
    }
  };

  const handleExecuteImport = async () => {
    if (!csvFile) return;
    if (!columnMapping.sku || !columnMapping.name || !columnMapping.price) {
      alert("Please map at least SKU, Product Name, and Price.");
      return;
    }
    setIsProcessingCsv(true);
    setCsvError(null);

    try {
      const result = await api.importMappedCsv(csvFile, columnMapping);
      setImportResult(result);
      setCsvStep("result");
      loadProducts();
    } catch (err: any) {
      setCsvError(err.message || "Failed to import mapped CSV");
    } finally {
      setIsProcessingCsv(false);
    }
  };

  const resetCsvModal = () => {
    setIsCsvOpen(false);
    setCsvStep("upload");
    setCsvFile(null);
    setPreviewData(null);
    setColumnMapping({});
    setImportResult(null);
    setCsvError(null);
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-serif font-bold text-white tracking-wide">
            Verified Jewellery Catalogue
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Grounded inventory database used by AI to generate verified prices and recommendations.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              setIsCsvOpen(true);
              setCsvStep("upload");
            }}
            className="px-3.5 py-2 rounded-xl bg-[#141824] hover:bg-[#1a2030] text-slate-200 border border-[#24293c] text-xs font-semibold flex items-center space-x-2 transition-all"
          >
            <Upload className="w-3.5 h-3.5 text-amber-400" />
            <span>Import Client CSV</span>
          </button>
          <button
            onClick={() => setIsAddOpen(true)}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs flex items-center space-x-1.5 shadow-lg shadow-amber-500/20 transition-all"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Jewellery Item</span>
          </button>
        </div>
      </div>

      {error && <p role="alert" className="rounded-xl border border-rose-400/30 p-4 text-sm text-rose-200">{error}<button onClick={loadProducts} className="ml-3 underline">Retry catalogue</button></p>}
      {loading && <p role="status" className="text-xs text-slate-400">Loading catalogue…</p>}

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-[#0f1118] border border-[#1e2333] flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Categories */}
        <div className="flex items-center space-x-1 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                selectedCategory === cat
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                  : "text-slate-400 hover:text-slate-200 hover:bg-[#151926]"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex items-center space-x-2 w-full md:w-64">
          <div className="relative w-full">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search SKU or name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-[#141824] border border-[#23283a] text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-400"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 rounded-xl bg-[#1a1f2e] text-xs text-slate-300 font-semibold border border-[#2b3247]"
          >
            Go
          </button>
        </form>
      </div>

      {/* Product Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {products.map((item) => {
          const primaryImg = item.images?.[0]?.image_url;
          return (
            <div
              key={item.id}
              className="rounded-2xl bg-[#0f1118] border border-[#1e2333] hover:border-amber-500/40 overflow-hidden flex flex-col justify-between transition-all group"
            >
              <div>
                {/* Image */}
                <div className="relative h-48 bg-[#161a26] overflow-hidden">
                  {primaryImg ? (
                    <img
                      src={primaryImg}
                      alt={item.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-slate-600">
                      <Gem className="w-10 h-10 opacity-40" />
                    </div>
                  )}
                  <span className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded text-[10px] font-bold bg-[#0d0f14]/80 text-amber-300 backdrop-blur-md border border-amber-500/20">
                    {item.gold_purity || "22K"}
                  </span>
                  <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded text-[10px] font-medium bg-[#0d0f14]/80 text-slate-300 backdrop-blur-md border border-[#262c3e]">
                    {item.sku}
                  </span>
                </div>

                {/* Details */}
                <div className="p-4 space-y-2">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span className="font-semibold text-amber-400">{item.category}</span>
                    {item.gross_weight && (
                      <span className="flex items-center space-x-1">
                        <Scale className="w-3 h-3" />
                        <span>{item.gross_weight}g</span>
                      </span>
                    )}
                  </div>

                  <h3 className="text-xs font-bold text-white group-hover:text-amber-300 transition-colors line-clamp-1">
                    {item.name}
                  </h3>

                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                    {item.description || "Certified hallmarked fine jewellery piece."}
                  </p>
                </div>
              </div>

              {/* Price & Action Footer */}
              <div className="p-4 pt-2 border-t border-[#181d2a] flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 block">Verified Price</span>
                  <span className="text-sm font-bold text-white tracking-tight">
                    {formatCurrency(item.price)}
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Stock: {item.stock}
                  </span>
                  <button
                    onClick={() => handleDelete(item.id)}
                    aria-label={`Delete ${item.name}`}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Add Product Modal */}
      {isAddOpen && (
        <div role="dialog" aria-modal="true" aria-labelledby="add-product-title" className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl bg-[#11141e] border border-[#22283a] p-6 space-y-4">
            <h3 id="add-product-title" className="text-base font-bold text-white font-serif">Add New Jewellery Item</h3>
            <form onSubmit={handleCreateProduct} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">SKU *</label>
                  <input
                    type="text"
                    aria-label="SKU"
                    required
                    placeholder="e.g. JW-RG-205"
                    value={formData.sku}
                    onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-xl bg-[#161a26] border border-[#242a3a] text-xs text-white"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">Category *</label>
                  <select
                    aria-label="Category"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-xl bg-[#161a26] border border-[#242a3a] text-xs text-white"
                  >
                    {["Rings", "Earrings", "Necklaces", "Bangles", "Bracelets", "Pendants", "Mangalsutras", "Coins"].map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Product Name *</label>
                <input
                  type="text"
                  aria-label="Product Name"
                  required
                  placeholder="e.g. 22K Royal Floral Gold Ring"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-1.5 rounded-xl bg-[#161a26] border border-[#242a3a] text-xs text-white"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">Price (₹ INR) *</label>
                  <input
                    type="number"
                    aria-label="Price (₹ INR)"
                    min="0"
                    step="0.01"
                    required
                    placeholder="25000"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-xl bg-[#161a26] border border-[#242a3a] text-xs text-white"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">Purity</label>
                  <select
                    aria-label="Purity"
                    value={formData.gold_purity}
                    onChange={(e) => setFormData({ ...formData, gold_purity: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-xl bg-[#161a26] border border-[#242a3a] text-xs text-white"
                  >
                    {["22K", "18K", "14K", "24K", "Platinum"].map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">Weight (g)</label>
                  <input
                    type="number"
                    aria-label="Weight (g)"
                    min="0"
                    step="0.01"
                    placeholder="4.2"
                    value={formData.gross_weight}
                    onChange={(e) => setFormData({ ...formData, gross_weight: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-xl bg-[#161a26] border border-[#242a3a] text-xs text-white"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="product-stock" className="text-[11px] text-slate-400 block mb-1">Available Stock</label>
                <input id="product-stock" type="number" min="0" step="1" required value={formData.stock} onChange={e => setFormData({ ...formData, stock: e.target.value })} className="w-full px-3 py-1.5 rounded-xl bg-[#161a26] border border-[#242a3a] text-xs text-white" />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Image URL</label>
                <input
                  type="url"
                  placeholder="https://images.unsplash.com/..."
                  value={formData.image_url}
                  onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                  className="w-full px-3 py-1.5 rounded-xl bg-[#161a26] border border-[#242a3a] text-xs text-white"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Description</label>
                <textarea
                  rows={2}
                  placeholder="Artisanal craftsmanship, BIS hallmarked..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-1.5 rounded-xl bg-[#161a26] border border-[#242a3a] text-xs text-white"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3">
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => setIsAddOpen(false)}
                  className="px-3.5 py-1.5 rounded-xl bg-[#1c2130] text-xs text-slate-300 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 text-xs font-bold"
                >
                  {saving ? "Saving..." : "Save Product"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CSV Import Modal with Client Column Mapping */}
      {isCsvOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-[#11141e] border border-[#22283a] p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-2 border-b border-[#1f2434]">
              <div className="flex items-center space-x-2">
                <FileSpreadsheet className="w-5 h-5 text-amber-400" />
                <h3 className="text-base font-bold text-white font-serif">
                  Client Jewellery Inventory CSV Import
                </h3>
              </div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Step {csvStep === "upload" ? "1/3" : csvStep === "map" ? "2/3" : "3/3"}
              </span>
            </div>

            {csvError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{csvError}</span>
              </div>
            )}

            {/* STEP 1: Upload File */}
            {csvStep === "upload" && (
              <form onSubmit={handleCsvPreview} className="space-y-4 pt-2">
                <p className="text-xs text-slate-400 leading-relaxed">
                  Upload your fine jewellery product catalog CSV. JewelAI will automatically detect your column names (ERP, Shopify, Tally or custom sheets) and provide a preview before importing.
                </p>

                <div className="p-6 rounded-2xl bg-[#141824] border-2 border-dashed border-[#282f44] hover:border-amber-500/40 text-center space-y-2 cursor-pointer transition-colors">
                  <Upload className="w-8 h-8 text-amber-400 mx-auto opacity-80" />
                  <div className="text-xs text-slate-300 font-medium">
                    {csvFile ? csvFile.name : "Select a jewellery CSV file"}
                  </div>
                  <input
                    type="file"
                    aria-label="Jewellery CSV file"
                    accept=".csv"
                    required={!csvFile}
                    onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                    className="w-full text-xs text-slate-400 file:mr-4 file:py-1.5 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-amber-500/10 file:text-amber-300 hover:file:bg-amber-500/20 cursor-pointer"
                  />
                </div>

                <div className="flex justify-end space-x-2 pt-2">
                  <button
                    type="button"
                    onClick={resetCsvModal}
                    className="px-4 py-2 rounded-xl bg-[#1c2130] text-xs text-slate-300 font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!csvFile || isProcessingCsv}
                    className="px-5 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 text-xs font-bold disabled:opacity-50 flex items-center space-x-1.5"
                  >
                    <span>{isProcessingCsv ? "Parsing..." : "Preview & Map Columns"}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </form>
            )}

            {/* STEP 2: Map Columns */}
            {csvStep === "map" && previewData && (
              <div className="space-y-4 pt-2">
                <p className="text-xs text-slate-400">
                  Review the detected column mappings for your CSV. Ensure required fields (SKU, Name, Price) match your file headers.
                </p>

                {/* Column Mapping Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-4 rounded-xl bg-[#141824] border border-[#23283a]">
                  {[
                    { key: "sku", label: "SKU / Design Code *", required: true },
                    { key: "name", label: "Product Name *", required: true },
                    { key: "price", label: "Selling Price (₹) *", required: true },
                    { key: "category", label: "Category (Rings, Earrings, etc.)" },
                    { key: "gold_purity", label: "Gold Purity (22K, 18K, etc.)" },
                    { key: "gross_weight", label: "Gross Weight in Grams" },
                    { key: "stock", label: "Available Stock / Qty" },
                    { key: "description", label: "Description / Specs" },
                    { key: "image_url", label: "Product Photograph URL" },
                  ].map((field) => (
                    <div key={field.key} className="space-y-1">
                      <label className="text-[11px] font-medium text-slate-300 flex items-center justify-between">
                        <span>{field.label}</span>
                        {field.required && <span className="text-amber-400 text-[10px]">Required</span>}
                      </label>
                      <select
                        value={columnMapping[field.key] || ""}
                        onChange={(e) =>
                          setColumnMapping({ ...columnMapping, [field.key]: e.target.value })
                        }
                        className="w-full px-2.5 py-1.5 rounded-lg bg-[#1a1f2e] border border-[#282f42] text-xs text-slate-200"
                      >
                        <option value="">-- Select matching CSV column --</option>
                        {previewData.headers.map((h) => (
                          <option key={h} value={h}>
                            {h}
                          </option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>

                {/* Sample Rows Preview */}
                {previewData.sample_rows.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider block">
                      Sample Data from Your File ({previewData.sample_rows.length} rows previewed)
                    </span>
                    <div className="overflow-x-auto max-h-36 rounded-xl border border-[#23283a] bg-[#141824]">
                      <table className="w-full text-left text-[11px]">
                        <thead className="bg-[#181d2a] text-slate-400">
                          <tr>
                            {previewData.headers.slice(0, 6).map((h) => (
                              <th key={h} className="p-2 font-medium whitespace-nowrap">
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#1e2332]">
                          {previewData.sample_rows.map((row, idx) => (
                            <tr key={idx} className="hover:bg-[#1a1f2e]">
                              {previewData.headers.slice(0, 6).map((h) => (
                                <td key={h} className="p-2 text-slate-300 whitespace-nowrap truncate max-w-[140px]">
                                  {row[h]}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                <div className="flex justify-between items-center pt-2">
                  <button
                    type="button"
                    onClick={() => setCsvStep("upload")}
                    className="px-4 py-2 rounded-xl bg-[#1c2130] text-xs text-slate-300 font-semibold"
                  >
                    Back
                  </button>
                  <button
                    type="button"
                    disabled={isProcessingCsv}
                    onClick={handleExecuteImport}
                    className="px-5 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 text-xs font-bold disabled:opacity-50 flex items-center space-x-1.5"
                  >
                    <span>{isProcessingCsv ? "Importing..." : "Execute Verified Import"}</span>
                  </button>
                </div>
              </div>
            )}

            {/* STEP 3: Results & Audit Summary */}
            {csvStep === "result" && importResult && (
              <div className="space-y-4 pt-2">
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs space-y-1">
                  <div className="flex items-center space-x-2 font-bold text-sm">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>CSV Import Completed</span>
                  </div>
                  <p>
                    Processed {importResult.total_processed} jewellery items: {importResult.imported_count} new items inserted, {importResult.updated_count} existing items updated.
                  </p>
                </div>

                {importResult.errors.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[11px] font-bold text-rose-300 uppercase tracking-wider block">
                      Row-Level Validation Notices ({importResult.errors.length})
                    </span>
                    <div className="max-h-32 overflow-y-auto p-3 rounded-xl bg-rose-500/5 border border-rose-500/20 text-[11px] text-rose-300 space-y-1">
                      {importResult.errors.map((err, i) => (
                        <div key={i}>{err}</div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex justify-end pt-2">
                  <button
                    type="button"
                    onClick={resetCsvModal}
                    className="px-5 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 text-xs font-bold"
                  >
                    Done & Refresh Catalogue
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
