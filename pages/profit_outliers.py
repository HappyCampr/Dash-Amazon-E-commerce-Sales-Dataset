from __future__ import annotations

import pandas as pd
import plotly.express as px
import dash
from dash import html, dcc, dash_table, Input, Output, callback

import data_store
from theme import get_theme, LIGHT_THEME

dash.register_page(__name__, path="/profit")


def layout(**_kwargs):
    return html.Div(
        children=[
            html.H3("Discount & Profit Outliers", style={"marginTop": "0"}),

            # KPI boxes (tables)
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"},
                children=[
                    html.Div(id="kpi_high_discount_box"),
                    html.Div(id="kpi_low_discount_box"),
                ],
            ),

            html.Div(style={"height": "12px"}),

            # Scatter quick win
            dcc.Graph(id="outliers_scatter"),

            html.Div(style={"height": "12px"}),

            # Flagged rows quick win
            html.H4(
                "Flagged rows: quantity=1 AND discount>0 AND payment is credit card",
                style={"marginBottom": "8px"},
            ),
            dash_table.DataTable(
                id="flagged_table",
                page_size=10,
                sort_action="native",
                filter_action="native",
                style_table={"overflowX": "auto"},
                style_cell={"padding": "8px", "fontSize": "12px", "whiteSpace": "nowrap"},
                style_header={"fontWeight": "bold"},
                style_data={},
                style_filter={},
            ),
        ]
    )


def _resolve_cols(dff: pd.DataFrame):
    product_col = "product_id" if "product_id" in dff.columns else None

    payment_col = None
    for c in ["payment_method", "payment_type", "payment", "pay_method"]:
        if c in dff.columns:
            payment_col = c
            break

    discount_col = None
    for c in ["discount", "discount_applied", "discount_amount"]:
        if c in dff.columns:
            discount_col = c
            break

    unit_price_col = "unit_price" if "unit_price" in dff.columns else None
    qty_col = "quantity" if "quantity" in dff.columns else None
    order_id_col = "order_id" if "order_id" in dff.columns else None

    total_sales_col = "total_sales" if "total_sales" in dff.columns else None

    return product_col, payment_col, discount_col, unit_price_col, qty_col, order_id_col, total_sales_col


def _ensure_total_sales(dff: pd.DataFrame, unit_price_col, qty_col, discount_col):
    """Add a derived total_sales if missing."""
    if "total_sales" in dff.columns and dff["total_sales"].notna().any():
        return dff

    dff = dff.copy()
    base = 0.0
    if unit_price_col and qty_col:
        base = dff[unit_price_col].fillna(0).astype(float) * dff[qty_col].fillna(0).astype(float)

    dff["total_sales"] = base

    # Subtract discount if it looks like dollars
    if discount_col and discount_col in dff.columns:
        dff["total_sales"] = dff["total_sales"] - dff[discount_col].fillna(0).astype(float)

    return dff


def _mode(series: pd.Series) -> str:
    s = series.dropna().astype(str)
    if s.empty:
        return ""
    m = s.mode()
    return m.iloc[0] if not m.empty else ""


def _build_kpi_table_box(title: str, rows_df: pd.DataFrame, theme: dict, product_col: str):
    cols = [
        {"name": "Product", "id": product_col},
        {"name": "Avg Discount", "id": "avg_discount"},
        {"name": "Avg Unit Price", "id": "avg_unit_price"},
        {"name": "Avg Qty / Order", "id": "avg_qty_per_order"},
        {"name": "Total Units Sold", "id": "total_units"},
        {"name": "Most Common Payment", "id": "most_common_payment"},
    ]

    out = rows_df.copy()
    for c in ["avg_discount", "avg_unit_price", "avg_qty_per_order"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").round(2)
    if "total_units" in out.columns:
        out["total_units"] = pd.to_numeric(out["total_units"], errors="coerce").fillna(0).astype(int)

    return html.Div(
        style={
            "border": f"2px solid {theme['accent_blue']}",
            "borderRadius": "10px",
            "padding": "12px",
            "backgroundColor": theme["card_bg"],
            "boxShadow": "0 2px 6px rgba(0,0,0,0.15)",
        },
        children=[
            html.Div(title, style={"fontWeight": "700", "marginBottom": "8px", "color": theme["text"]}),
            dash_table.DataTable(
                data=out.to_dict("records"),
                columns=cols,
                style_table={"overflowX": "auto"},
                style_cell={
                    "padding": "6px",
                    "fontSize": "12px",
                    "whiteSpace": "nowrap",
                    "backgroundColor": theme["container_bg"],
                    "color": theme["text"],
                    "border": f"1px solid {theme['border']}",
                },
                style_header={
                    "fontWeight": "bold",
                    "backgroundColor": theme["card_bg"],
                    "color": theme["text"],
                    "border": f"1px solid {theme['border']}",
                },
                style_data={
                    "backgroundColor": theme["container_bg"],
                    "color": theme["text"],
                },
                style_filter={
                    "backgroundColor": theme["container_bg"],
                    "color": theme["text"],
                },
            ),
        ],
    )


@callback(
    Output("kpi_high_discount_box", "children"),
    Output("kpi_low_discount_box", "children"),
    Output("outliers_scatter", "figure"),
    Output("flagged_table", "data"),
    Output("flagged_table", "columns"),
    Output("flagged_table", "style_table"),
    Output("flagged_table", "style_cell"),
    Output("flagged_table", "style_header"),
    Output("flagged_table", "style_data"),
    Output("flagged_table", "style_filter"),
    Input("category", "value"),
    Input("state", "value"),
    Input("sub_category", "value"),
    Input("date_range", "start_date"),
    Input("date_range", "end_date"),
    Input("theme-store", "data"),
)
def update_profit_outliers(category, state, sub_category, start_date, end_date, current_theme):
    df_all = data_store.df_all
    chart_template = "plotly_dark" if current_theme == "dark" else "plotly"
    theme = get_theme(current_theme)

    table_style_table = {
        "overflowX": "auto",
        "backgroundColor": theme["container_bg"],
    }

    table_style_cell = {
        "padding": "8px",
        "fontSize": "12px",
        "whiteSpace": "nowrap",
        "backgroundColor": theme["container_bg"],
        "color": theme["text"],
        "border": f"1px solid {theme['border']}",
    }

    table_style_header = {
        "fontWeight": "bold",
        "backgroundColor": theme["card_bg"],
        "color": theme["text"],
        "border": f"1px solid {theme['border']}",
    }

    table_style_data = {
        "backgroundColor": theme["container_bg"],
        "color": theme["text"],
    }

    table_style_filter = {
        "backgroundColor": theme["container_bg"],
        "color": theme["text"],
    }

    if df_all is None:
        empty_fig = px.scatter(title="Data not loaded (data_store.df_all is None)", template=chart_template)
        empty_box = html.Div("Data not loaded. Check app.py sets data_store.df_all.", style={"padding": "12px", "color": theme["text"]})
        return (
            empty_box,
            empty_box,
            empty_fig,
            [],
            [],
            table_style_table,
            table_style_cell,
            table_style_header,
            table_style_data,
            table_style_filter,
        )

    dff = df_all.copy()

    # Apply shared filters (only if cols exist)
    if category and "category" in dff.columns:
        dff = dff[dff["category"].astype(str) == str(category)]
    if state and "state" in dff.columns:
        dff = dff[dff["state"].astype(str) == str(state)]
    if sub_category and "sub_category" in dff.columns:
        dff = dff[dff["sub_category"].astype(str) == str(sub_category)]

    if "order_date" in dff.columns and start_date and end_date:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        dff = dff[(dff["order_date"].notna()) & (dff["order_date"] >= start) & (dff["order_date"] <= end)]

    # Resolve columns + ensure total_sales exists
    product_col, payment_col, discount_col, unit_price_col, qty_col, order_id_col, _ = _resolve_cols(dff)
    dff = _ensure_total_sales(dff, unit_price_col, qty_col, discount_col)

    # Empty state
    if dff.empty or not product_col or not discount_col:
        empty_fig = px.scatter(title="No data for current filters", template=chart_template)
        empty_box = html.Div("No data available for these filters.", style={"padding": "12px", "opacity": 0.8, "color": theme["text"]})
        return (
            empty_box,
            empty_box,
            empty_fig,
            [],
            [],
            table_style_table,
            table_style_cell,
            table_style_header,
            table_style_data,
            table_style_filter,
        )

    # --- KPI computation: top/bottom 5 products by average discount ---
    if order_id_col and qty_col:
        per_order_qty = dff.groupby([product_col, order_id_col])[qty_col].sum().reset_index(name="qty_in_order")
        avg_qty_per_order = per_order_qty.groupby(product_col)["qty_in_order"].mean().reset_index(name="avg_qty_per_order")
    else:
        if qty_col:
            avg_qty_per_order = dff.groupby(product_col)[qty_col].mean().reset_index(name="avg_qty_per_order")
        else:
            avg_qty_per_order = pd.DataFrame({product_col: dff[product_col].unique(), "avg_qty_per_order": 0})

    if qty_col:
        total_units = dff.groupby(product_col)[qty_col].sum().reset_index(name="total_units")
    else:
        total_units = dff.groupby(product_col).size().reset_index(name="total_units")

    if unit_price_col:
        avg_unit_price = dff.groupby(product_col)[unit_price_col].mean().reset_index(name="avg_unit_price")
    else:
        avg_unit_price = dff.groupby(product_col).size().reset_index(name="avg_unit_price")
        avg_unit_price["avg_unit_price"] = 0

    avg_discount = dff.groupby(product_col)[discount_col].mean().reset_index(name="avg_discount")

    if payment_col:
        mode_payment = dff.groupby(product_col)[payment_col].agg(_mode).reset_index(name="most_common_payment")
    else:
        mode_payment = pd.DataFrame({product_col: dff[product_col].unique(), "most_common_payment": ""})

    kpi_df = (
        avg_discount
        .merge(avg_unit_price, on=product_col, how="left")
        .merge(avg_qty_per_order, on=product_col, how="left")
        .merge(total_units, on=product_col, how="left")
        .merge(mode_payment, on=product_col, how="left")
    )

    top5 = kpi_df.sort_values("avg_discount", ascending=False).head(5)
    bot5 = kpi_df.sort_values("avg_discount", ascending=True).head(5)

    high_box = _build_kpi_table_box("Top 5 products with the highest average discount", top5, theme, product_col)
    low_box = _build_kpi_table_box("Top 5 products with the lowest average discount", bot5, theme, product_col)

    # --- Scatter: discount vs total_sales colored by payment method ---
    color_arg = payment_col if payment_col else None
    hover_cols = [c for c in [product_col, qty_col, unit_price_col, discount_col, "total_sales"] if c and c in dff.columns]

    fig = px.scatter(
        dff,
        x=discount_col,
        y="total_sales",
        color=color_arg,
        hover_data=hover_cols,
        title="Discount vs Total Sales (filtered)",
        template=chart_template,
    )
    fig.update_layout(hovermode="closest")

    # --- Flagged table: qty=1 AND discount>0 AND payment is credit/card ---
    flagged = dff.copy()

    if qty_col and qty_col in flagged.columns:
        flagged = flagged[flagged[qty_col].fillna(0).astype(float) == 1]

    flagged = flagged[flagged[discount_col].fillna(0).astype(float) > 0]

    if payment_col and payment_col in flagged.columns:
        p = flagged[payment_col].fillna("").astype(str).str.lower()
        flagged = flagged[p.str.contains("credit") | p.str.contains("card")]

    flagged = flagged.head(300)

    preferred_cols = [
        "order_id",
        "order_date",
        "customer_id",
        "state",
        "product_id",
        "category",
        "sub_category",
        "brand",
        "quantity",
        "unit_price",
        "discount",
        "shipping_cost",
        "total_sales",
        "payment_method",
    ]

    show_cols = [c for c in preferred_cols if c and c in flagged.columns]
    flagged_view = flagged[show_cols].copy() if show_cols else flagged.copy()

    cols = [{"name": c, "id": c} for c in flagged_view.columns]
    data = flagged_view.to_dict("records")

    return (
        high_box,
        low_box,
        fig,
        data,
        cols,
        table_style_table,
        table_style_cell,
        table_style_header,
        table_style_data,
        table_style_filter,
    )