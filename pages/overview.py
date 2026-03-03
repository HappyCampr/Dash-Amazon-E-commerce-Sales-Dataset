# pages/overview.py
from __future__ import annotations

import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, dash_table, Input, Output, callback

import data_store
from theme import get_theme, LIGHT_THEME

dash.register_page(__name__, path="/")


def kpi_card(label: str, value: str, theme: dict | None = None) -> html.Div:
    if theme is None:
        theme = LIGHT_THEME

    return html.Div(
        style={
            "border": f"2px solid {theme['accent_blue']}",
            "borderRadius": "10px",
            "padding": "12px",
            "backgroundColor": theme["card_bg"],
            "boxShadow": "0 2px 4px rgba(44, 125, 215, 0.1)",
        },
        children=[
            html.Div(
                label,
                style={
                    "fontSize": "12px",
                    "opacity": 0.75,
                    "color": theme["text"],
                    "fontWeight": "500",
                },
            ),
            html.Div(
                value,
                style={
                    "fontSize": "22px",
                    "fontWeight": "bold",
                    "marginTop": "6px",
                    "color": theme["text"],
                },
            ),
        ],
    )


def layout(**_kwargs):
    return html.Div(
        children=[
            html.Div(id="top_product_card", style={"marginBottom": "18px"}),

            html.Div(
                id="kpi_row",
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr 1fr 1fr",
                    "gap": "12px",
                },
            ),

            html.Div(style={"height": "12px"}),

            html.Div(
                style={"display": "grid", "gridTemplateColumns": "2fr 1fr", "gap": "12px"},
                children=[dcc.Graph(id="sales_trend"), dcc.Graph(id="category_bar")],
            ),

            html.Div(style={"height": "12px"}),

            html.Div(
                style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"},
                children=[dcc.Graph(id="discount_scatter"), dcc.Graph(id="payment_pie")],
            ),

            html.Hr(),
            html.H3("Filtered Orders"),

            dash_table.DataTable(
                id="table",
                page_size=10,
                sort_action="native",
                filter_action="native",
                style_table={"overflowX": "auto"},
                style_cell={"padding": "8px", "fontSize": "12px", "whiteSpace": "nowrap"},
                style_header={"fontWeight": "bold"},
                style_data={},
            ),
        ]
    )


@callback(
    Output("top_product_card", "children"),
    Output("kpi_row", "children"),
    Output("sales_trend", "figure"),
    Output("category_bar", "figure"),
    Output("discount_scatter", "figure"),
    Output("payment_pie", "figure"),
    Output("table", "data"),
    Output("table", "columns"),
    Output("table", "style_table"),
    Output("table", "style_cell"),
    Output("table", "style_header"),
    Output("table", "style_data"),
    Output("date_hint", "children"),
    Input("category", "value"),
    Input("state", "value"),
    Input("sub_category", "value"),
    Input("date_range", "start_date"),
    Input("date_range", "end_date"),
    Input("theme-store", "data"),
)
def update_dashboard(category, state, sub_category, start_date, end_date, current_theme):
    # IMPORTANT: df_all comes from data_store (set in app.py)
    df_all = data_store.df_all
    theme = get_theme(current_theme)

    # Table style dicts (theme-aware)
    table_style_table = {"overflowX": "auto", "backgroundColor": theme["container_bg"]}
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
    table_style_data = {"backgroundColor": theme["container_bg"], "color": theme["text"]}

    if df_all is None:
        # If app.py forgot to set it, fail gracefully
        empty_fig = px.scatter(title="Data not loaded")
        return (
            html.Div("Data not loaded. Check data_store.df_all.", style={"padding": "12px", "color": theme["text"]}),
            [],
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            [],
            [],
            table_style_table,
            table_style_cell,
            table_style_header,
            table_style_data,
            "Data not loaded.",
        )
    dff = df_all.copy()

    # Filters
    if category and "category" in dff.columns:
        dff = dff[dff["category"].astype(str) == str(category)]
    if state and "state" in dff.columns:
        dff = dff[dff["state"].astype(str) == str(state)]
    if sub_category and "sub_category" in dff.columns:
        dff = dff[dff["sub_category"].astype(str) == str(sub_category)]

    # Date filter
    date_hint = ""
    if "order_date" in dff.columns and start_date and end_date:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        dff = dff[(dff["order_date"].notna()) & (dff["order_date"] >= start) & (dff["order_date"] <= end)]
        date_hint = f"Showing orders from {start.date()} to {end.date()}"

    chart_template = "plotly_dark" if current_theme == "dark" else "plotly"

    if dff.empty:
        empty_fig = px.scatter(title="No data for current filters", template=chart_template)
        empty_product_card = html.Div(
            "No data for top product",
            style={"fontSize": "12px", "opacity": 0.7, "padding": "12px", "color": theme["text"]},
        )
        return (
            empty_product_card,
            [
                kpi_card("Orders", "0", theme),
                kpi_card("Revenue", "$0", theme),
                kpi_card("AOV", "$0", theme),
                kpi_card("Units", "0", theme),
            ],
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            [],
            [],
            table_style_table,
            table_style_cell,
            table_style_header,
            table_style_data,
            "No rows match your filters.",
        )

    # Revenue calc
    if "total_sales" in dff.columns and dff["total_sales"].notna().any():
        revenue = float(dff["total_sales"].fillna(0).sum())
    else:
        revenue = 0.0
        if "quantity" in dff.columns and "unit_price" in dff.columns:
            revenue = float((dff["quantity"].fillna(0) * dff["unit_price"].fillna(0)).sum())
        if "discount" in dff.columns:
            revenue -= float(dff["discount"].fillna(0).sum())

    orders = dff["order_id"].nunique() if "order_id" in dff.columns else len(dff)
    units = int(dff["quantity"].fillna(0).sum()) if "quantity" in dff.columns else 0
    aov = revenue / orders if orders else 0.0

    # Top product card
    top_product_card_content = html.Div()
    if "product_id" in dff.columns and "total_sales" in dff.columns:
        prod_sales = dff.groupby("product_id", as_index=False)["total_sales"].sum()
        if not prod_sales.empty:
            top_prod = prod_sales.loc[prod_sales["total_sales"].idxmax()]
            top_product_id = top_prod["product_id"]
            prod_df = dff[dff["product_id"] == top_product_id].copy()
            total_sales = prod_df["total_sales"].sum()

            if "order_date" in prod_df.columns and prod_df["order_date"].notna().any():
                date_range_days = (prod_df["order_date"].max() - prod_df["order_date"].min()).days + 1
                monthly_avg = (total_sales * 30) / max(date_range_days, 1)
                weekly_avg = (total_sales * 7) / max(date_range_days, 1)
                daily_avg = total_sales / max(date_range_days, 1)
            else:
                monthly_avg = weekly_avg = daily_avg = 0

            top_product_card_content = html.Div(
                style={
                    "border": f"2px solid {theme['accent_dark_blue']}",
                    "borderRadius": "10px",
                    "padding": "16px",
                    "backgroundColor": theme["card_bg"],
                    "boxShadow": "0 2px 6px rgba(0,0,0,0.2)",
                },
                children=[
                    html.H4(
                        f"Top Product: {top_product_id}",
                        style={"margin": "0 0 12px 0", "color": theme["text"], "fontWeight": "600"},
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr 1fr", "gap": "12px"},
                        children=[
                            html.Div(
                                children=[
                                    html.Div("Total Gross Sales", style={"fontSize": "11px", "opacity": 0.75, "color": theme["text"]}),
                                    html.Div(f"${total_sales:,.2f}", style={"fontSize": "18px", "fontWeight": "bold", "color": theme["text"]}),
                                ]
                            ),
                            html.Div(
                                children=[
                                    html.Div("Monthly Avg", style={"fontSize": "11px", "opacity": 0.75, "color": theme["text"]}),
                                    html.Div(f"${monthly_avg:,.2f}", style={"fontSize": "18px", "fontWeight": "bold", "color": theme["text"]}),
                                ]
                            ),
                            html.Div(
                                children=[
                                    html.Div("Weekly Avg", style={"fontSize": "11px", "opacity": 0.75, "color": theme["text"]}),
                                    html.Div(f"${weekly_avg:,.2f}", style={"fontSize": "18px", "fontWeight": "bold", "color": theme["text"]}),
                                ]
                            ),
                            html.Div(
                                children=[
                                    html.Div("Daily Avg", style={"fontSize": "11px", "opacity": 0.75, "color": theme["text"]}),
                                    html.Div(f"${daily_avg:,.2f}", style={"fontSize": "18px", "fontWeight": "bold", "color": theme["text"]}),
                                ]
                            ),
                        ],
                    ),
                ],
            )

    kpis = [
        kpi_card("Orders", f"{orders:,}", theme),
        kpi_card("Revenue", f"${revenue:,.2f}", theme),
        kpi_card("AOV", f"${aov:,.2f}", theme),
        kpi_card("Units", f"{units:,}", theme),
    ]

    # Trend
    if "order_date" in dff.columns and dff["order_date"].notna().any():
        if "total_sales" in dff.columns:
            trend = (
                dff.assign(day=dff["order_date"].dt.to_period("D").dt.to_timestamp())
                .groupby("day", as_index=False)["total_sales"]
                .sum()
            )
            y_col = "total_sales"
        else:
            tmp = dff.assign(day=dff["order_date"].dt.to_period("D").dt.to_timestamp())
            tmp["derived_sales"] = tmp.get("quantity", 0).fillna(0) * tmp.get("unit_price", 0).fillna(0)
            trend = tmp.groupby("day", as_index=False)["derived_sales"].sum()
            y_col = "derived_sales"

        sales_trend_fig = px.line(trend, x="day", y=y_col, markers=True, title="Revenue Trend (Daily)", template=chart_template)
        sales_trend_fig.update_layout(hovermode="x unified")
    else:
        sales_trend_fig = px.scatter(title="Order date missing", template=chart_template)

    # Category bar
    if "category" in dff.columns:
        if "total_sales" in dff.columns:
            cat = dff.groupby("category", as_index=False)["total_sales"].sum()
            y_col = "total_sales"
        else:
            tmp = dff.copy()
            tmp["derived_sales"] = tmp.get("quantity", 0).fillna(0) * tmp.get("unit_price", 0).fillna(0)
            cat = tmp.groupby("category", as_index=False)["derived_sales"].sum()
            y_col = "derived_sales"

        category_bar_fig = px.bar(
            cat.sort_values(y_col, ascending=False).head(12),
            x="category",
            y=y_col,
            title="Top Categories by Revenue",
            template=chart_template,
        )
    else:
        category_bar_fig = px.scatter(title="Category not found", template=chart_template)

    # Discount scatter
    if all(c in dff.columns for c in ["discount", "total_sales"]):
        discount_scatter_fig = px.scatter(
            dff,
            x="discount",
            y="total_sales",
            title="Discount vs Total Sales",
            template=chart_template,
        )
    else:
        discount_scatter_fig = px.scatter(title="Discount vs Sales (columns missing)", template=chart_template)

    # Payment pie
    vibrant_colors = ["#2c7dd7", "#1bb083", "#1ca5b6", "#a9326c", "#7953de", "#f8d0b6", "#f2b992", "#1590a1", "#5165e1", "#236ac1"]
    if "payment_method" in dff.columns:
        pay = dff["payment_method"].fillna("Unknown").astype(str).value_counts().reset_index()
        pay.columns = ["payment_method", "count"]
        payment_pie_fig = px.pie(
            pay,
            names="payment_method",
            values="count",
            title="Payment Method Mix",
            color_discrete_sequence=vibrant_colors,
            template=chart_template,
        )
    else:
        payment_pie_fig = px.pie(
            names=["Unknown"],
            values=[1],
            title="Payment Method Mix (missing column)",
            color_discrete_sequence=vibrant_colors,
            template=chart_template,
        )

    # Table
    show_cols = [c for c in [
        "order_id", "order_date", "customer_id", "state", "city",
        "product_id", "category", "sub_category", "brand",
        "quantity", "unit_price", "discount", "shipping_cost", "total_sales",
        "payment_method", "order_status"
    ] if c in dff.columns]

    table_df = dff[show_cols].copy() if show_cols else dff.head(50).copy()
    for c in table_df.columns:
        if pd.api.types.is_datetime64_any_dtype(table_df[c]):
            table_df[c] = table_df[c].dt.strftime("%Y-%m-%d")

    columns = [{"name": c, "id": c} for c in table_df.columns]
    data = table_df.head(500).to_dict("records")

    return (
        top_product_card_content,
        kpis,
        sales_trend_fig,
        category_bar_fig,
        discount_scatter_fig,
        payment_pie_fig,
        data,
        columns,
        table_style_table,
        table_style_cell,
        table_style_header,
        table_style_data,
        date_hint,
    )