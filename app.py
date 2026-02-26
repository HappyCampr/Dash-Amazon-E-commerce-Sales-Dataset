from __future__ import annotations

import os
import pandas as pd
import plotly.express as px

from dash import Dash, dcc, html, Input, Output, dash_table



DATA_PATH = os.path.join("dataset", "amazon_sales_dataset.csv")


def load_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"CSV not found at: {path}\n"
            f"Expected it at: dataset/amazon_sales_dataset.csv"
        )

    df = pd.read_csv(path)

    # --- Normalize column names (optional but helps) ---
    df.columns = [c.strip() for c in df.columns]

    # --- Parse dates if present ---
    for col in ["order_date", "ship_date", "delivery_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # --- Ensure numeric columns are numeric if present ---
    numeric_cols = ["quantity", "unit_price", "discount", "shipping_cost", "total_sales"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def safe_unique_sorted(df: pd.DataFrame, col: str) -> list:
    if col not in df.columns:
        return []
    vals = df[col].dropna().astype(str).unique().tolist()
    return sorted(vals)


# Theme color schemes
LIGHT_THEME = {
    "bg": "#ffffff",
    "text": "#000000",
    "container_bg": "#ffffff",
    "border": "#ddd",
    "card_bg": "#f0f6ff",
    "card_border": "#2c7dd7",
    "accent_blue": "#2c7dd7",
    "accent_green": "#1bb083",
    "accent_dark_blue": "#1957ab",
}

DARK_THEME = {
    "bg": "#1a1a1a",
    "text": "#e8e8e8",
    "container_bg": "#242424",
    "border": "#404040",
    "card_bg": "#303030",
    "card_border": "#5ba3e8",
    "accent_blue": "#5ba3e8",
    "accent_green": "#4dd7a8",
    "accent_dark_blue": "#5b87d4",
}

def get_theme(theme_name: str) -> dict:
    return DARK_THEME if theme_name == "dark" else LIGHT_THEME


df_all = load_data(DATA_PATH)

# Default date bounds (based on order_date if available)
if "order_date" in df_all.columns and df_all["order_date"].notna().any():
    min_date = df_all["order_date"].min().date()
    max_date = df_all["order_date"].max().date()
else:
    min_date, max_date = None, None

# Dropdown options
category_options = safe_unique_sorted(df_all, "category")
state_options = safe_unique_sorted(df_all, "state")
sub_category_options = safe_unique_sorted(df_all, "sub_category")

app = Dash(__name__)
app.title = "Amazon Sales Dashboard"

app.layout = html.Div(
    id="main-container",
    style={
        "minHeight": "100vh",
        "backgroundColor": "#ffffff",
        "color": "#000000",
        "fontFamily": "Arial",
        "transition": "background-color 0.3s, color 0.3s",
    },
    children=[
        dcc.Store(id="theme-store", data="light"),
        html.Div(
            style={
                "maxWidth": "1200px",
                "margin": "18px auto",
                "position": "relative",
            },
            children=[
                html.Div(
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "marginBottom": "18px",
                    },
                    children=[
                        html.H2(
                            "Amazon E-commerce Sales — Dash App",
                            style={"margin": "0"},
                        ),
                        html.Button(
                            "🌙 Dark Mode",
                            id="theme-toggle-btn",
                            n_clicks=0,
                            style={
                                "padding": "8px 16px",
                                "borderRadius": "6px",
                                "border": "2px solid #2c7dd7",
                                "backgroundColor": "#f0f6ff",
                                "color": "#000000",
                                "fontSize": "12px",
                                "fontWeight": "600",
                                "cursor": "pointer",
                                "transition": "all 0.3s",
                            },
                        ),
                    ],
                ),
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "1fr 1fr 1fr",
                        "gap": "12px",
                        "alignItems": "end",
                    },
                    children=[
                        html.Div(
                            children=[
                                html.Label("Category"),
                                dcc.Dropdown(
                                    id="category",
                                    options=[{"label": c, "value": c} for c in category_options],
                                    value=None,
                                    clearable=True,
                                    placeholder="All categories",
                                ),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Label("State"),
                                dcc.Dropdown(
                                    id="state",
                                    options=[{"label": c, "value": c} for c in state_options],
                                    value=None,
                                    clearable=True,
                                    placeholder="All states",
                                ),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Label("Sub Category"),
                                dcc.Dropdown(
                                    id="sub_category",
                                    options=[{"label": s, "value": s} for s in sub_category_options],
                                    value=None,
                                    clearable=True,
                                    placeholder="All sub categories",
                                ),
                            ]
                        ),
                    ],
                ),

        html.Div(style={"height": "10px"}),

        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr", "gap": "12px"},
            children=[
                html.Div(
                    children=[
                        html.Label("Order date range"),
                        dcc.DatePickerRange(
                            id="date_range",
                            min_date_allowed=min_date,
                            max_date_allowed=max_date,
                            start_date=min_date,
                            end_date=max_date,
                            display_format="YYYY-MM-DD",
                        ),
                        html.Div(
                            id="date_hint",
                            style={"fontSize": "12px", "opacity": 0.7, "marginTop": "6px"},
                        ),
                    ]
                )
            ],
        ),

        html.Hr(),

        # Top Product Card
        html.Div(
            id="top_product_card",
            style={"marginBottom": "18px"},
        ),

        # KPI row
        html.Div(
            id="kpi_row",
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr 1fr 1fr",
                "gap": "12px",
            },
        ),

        html.Div(style={"height": "12px"}),

        # Charts
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "2fr 1fr", "gap": "12px"},
            children=[
                dcc.Graph(id="sales_trend"),
                dcc.Graph(id="category_bar"),
            ],
        ),

        html.Div(style={"height": "12px"}),

        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"},
            children=[
                dcc.Graph(id="discount_scatter"),
                dcc.Graph(id="payment_pie"),
            ],
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
    ],
        ),
    ],
)


def kpi_card(label: str, value: str, theme: dict | None = None) -> html.Div:
    if theme is None:
        theme = LIGHT_THEME
    
    return html.Div(
        style={
            "border": f"2px solid {theme['accent_blue']}",
            "borderRadius": "10px",
            "padding": "12px",
            "backgroundColor": theme["card_bg"],
            "boxShadow": f"0 2px 4px rgba(44, 125, 215, 0.1)",
        },
        children=[
            html.Div(label, style={"fontSize": "12px", "opacity": 0.75, "color": theme["text"], "fontWeight": "500"}),
            html.Div(value, style={"fontSize": "22px", "fontWeight": "bold", "marginTop": "6px", "color": theme["text"]}),
        ],
    )


# Theme toggle callback
@app.callback(
    Output("theme-store", "data"),
    Output("theme-toggle-btn", "children"),
    Output("theme-toggle-btn", "style"),
    Output("main-container", "style"),
    Input("theme-toggle-btn", "n_clicks"),
    Input("theme-store", "data"),
)
def toggle_theme(n_clicks, current_theme):
    # On initial load, don't flip
    if not n_clicks:
        theme = get_theme(current_theme)
        btn_text = "☀️ Light Mode" if current_theme == "dark" else "🌙 Dark Mode"
        btn_style = {
            "padding": "8px 16px",
            "borderRadius": "6px",
            "border": f"2px solid {theme['accent_blue']}",
            "backgroundColor": theme["card_bg"],
            "color": theme["text"],
            "fontSize": "12px",
            "fontWeight": "600",
            "cursor": "pointer",
            "transition": "all 0.3s",
        }
        container_style = {
            "minHeight": "100vh",
            "backgroundColor": theme["bg"],
            "color": theme["text"],
            "fontFamily": "Arial",
            "transition": "background-color 0.3s, color 0.3s",
        }
        return current_theme, btn_text, btn_style, container_style

    new_theme = "dark" if current_theme == "light" else "light"
    theme = get_theme(new_theme)

    btn_style = {
        "padding": "8px 16px",
        "borderRadius": "6px",
        "border": f"2px solid {theme['accent_blue']}",
        "backgroundColor": theme["card_bg"],
        "color": theme["text"],
        "fontSize": "12px",
        "fontWeight": "600",
        "cursor": "pointer",
        "transition": "all 0.3s",
    }
    btn_text = "☀️ Light Mode" if new_theme == "dark" else "🌙 Dark Mode"
    container_style = {
        "minHeight": "100vh",
        "backgroundColor": theme["bg"],
        "color": theme["text"],
        "fontFamily": "Arial",
        "transition": "background-color 0.3s, color 0.3s",
    }
    return new_theme, btn_text, btn_style, container_style


# Table styles based on theme
@app.callback(
    Output("table", "style_table"),
    Output("table", "style_cell"),
    Output("table", "style_header"),
    Output("table", "style_data"),
    Input("theme-store", "data"),
)
def update_table_styles(current_theme):
    theme = get_theme(current_theme)
    
    style_table = {
        "overflowX": "auto",
        "backgroundColor": theme["container_bg"],
    }
    
    style_cell = {
        "padding": "8px",
        "fontSize": "12px",
        "whiteSpace": "nowrap",
        "backgroundColor": theme["container_bg"],
        "color": theme["text"],
        "border": f"1px solid {theme['border']}",
    }
    
    style_header = {
        "fontWeight": "bold",
        "backgroundColor": theme["card_bg"],
        "color": theme["text"],
        "border": f"1px solid {theme['border']}",
    }
    
    style_data = {
        "backgroundColor": theme["container_bg"],
        "color": theme["text"],
    }
    
    return style_table, style_cell, style_header, style_data


# Dependent dropdown callbacks
@app.callback(
    Output("category", "style"),
    Output("state", "style"),
    Output("sub_category", "style"),
    Output("date_range", "style"),
    Input("theme-store", "data"),
)
def update_dropdown_styles(current_theme):
    theme = get_theme(current_theme)
    # If dropdown background is white, use black text; otherwise use theme text
    dropdown_bg = "#ffffff" if current_theme == "light" else theme["card_bg"]
    text_color = "#000000" if dropdown_bg.lower() in ("#ffffff", "#fff") else theme["text"]
    style = {
        "backgroundColor": dropdown_bg,
        "color": text_color,
        "border": f"1px solid {theme['border']}",
        "borderRadius": "6px",
        "padding": "6px",
    }
    # DatePickerRange expects style dict as well
    date_style = {"backgroundColor": dropdown_bg, "color": text_color}
    return style, style, style, date_style

@app.callback(
    Output("state", "options"),
    Input("category", "value"),
    Input("sub_category", "value"),
)
def update_state_options(category, sub_category):
    filtered_df = df_all.copy()
    
    if category:
        filtered_df = filtered_df[filtered_df["category"].astype(str) == str(category)]
    if sub_category:
        filtered_df = filtered_df[filtered_df["sub_category"].astype(str) == str(sub_category)]
    
    state_opts = safe_unique_sorted(filtered_df, "state")
    options = [{"label": s, "value": s} for s in state_opts]
    
    return options


@app.callback(
    Output("sub_category", "options"),
    Input("category", "value"),
    Input("state", "value"),
)
def update_sub_category_options(category, state):
    filtered_df = df_all.copy()
    
    if category:
        filtered_df = filtered_df[filtered_df["category"].astype(str) == str(category)]
    if state:
        filtered_df = filtered_df[filtered_df["state"].astype(str) == str(state)]
    
    sub_cat_opts = safe_unique_sorted(filtered_df, "sub_category")
    options = [{"label": s, "value": s} for s in sub_cat_opts]
    
    return options


@app.callback(
    Output("category", "options"),
    Input("state", "value"),
    Input("sub_category", "value"),
)
def update_category_options(state, sub_category):
    filtered_df = df_all.copy()
    
    if state:
        filtered_df = filtered_df[filtered_df["state"].astype(str) == str(state)]
    if sub_category:
        filtered_df = filtered_df[filtered_df["sub_category"].astype(str) == str(sub_category)]
    
    cat_opts = safe_unique_sorted(filtered_df, "category")
    options = [{"label": c, "value": c} for c in cat_opts]
    
    return options


@app.callback(
    Output("top_product_card", "children"),
    Output("kpi_row", "children"),
    Output("sales_trend", "figure"),
    Output("category_bar", "figure"),
    Output("discount_scatter", "figure"),
    Output("payment_pie", "figure"),
    Output("table", "data"),
    Output("table", "columns"),
    Output("date_hint", "children"),
    Input("category", "value"),
    Input("state", "value"),
    Input("sub_category", "value"),
    Input("date_range", "start_date"),
    Input("date_range", "end_date"),
    Input("theme-store", "data"),
)
def update_dashboard(category, state, sub_category, start_date, end_date, current_theme):
    theme = get_theme(current_theme)
    dff = df_all.copy()

    # Filters (only apply if column exists)
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

    if dff.empty:
        # Empty-state visuals
        empty_fig = px.scatter(title="No data for current filters")
        empty_product_card = html.Div("No data for top product", style={"fontSize": "12px", "opacity": 0.7, "padding": "12px", "color": theme["text"]})
        return (
            empty_product_card,
            [kpi_card("Orders", "0", theme), kpi_card("Revenue", "$0", theme), kpi_card("AOV", "$0", theme), kpi_card("Units", "0", theme)],
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            [],
            [],
            "No rows match your filters.",
        )

    # KPI calculations (use total_sales if present; else derive from quantity * unit_price - discount if possible)
    if "total_sales" in dff.columns and dff["total_sales"].notna().any():
        revenue = float(dff["total_sales"].fillna(0).sum())
    else:
        revenue = 0.0
        if "quantity" in dff.columns and "unit_price" in dff.columns:
            revenue = float((dff["quantity"].fillna(0) * dff["unit_price"].fillna(0)).sum())
        if "discount" in dff.columns:
            # If discount is percent-like, you’ll adjust later; for now subtract raw values if present
            revenue -= float(dff["discount"].fillna(0).sum())

    orders = dff["order_id"].nunique() if "order_id" in dff.columns else len(dff)
    units = int(dff["quantity"].fillna(0).sum()) if "quantity" in dff.columns else 0
    aov = revenue / orders if orders else 0.0

    # Top Product Card
    top_product_card_content = html.Div()
    if "product_id" in dff.columns and "total_sales" in dff.columns:
        prod_sales = dff.groupby("product_id", as_index=False)["total_sales"].sum()
        if not prod_sales.empty:
            top_prod = prod_sales.loc[prod_sales["total_sales"].idxmax()]
            top_product_id = top_prod["product_id"]
            
            # Get all records for this product
            prod_df = dff[dff["product_id"] == top_product_id].copy()
            total_sales = prod_df["total_sales"].sum()
            
            # Calculate averages
            if "order_date" in prod_df.columns and prod_df["order_date"].notna().any():
                date_range_days = (prod_df["order_date"].max() - prod_df["order_date"].min()).days + 1
                monthly_avg = (total_sales * 30) / max(date_range_days, 1)  # Annualize to monthly
                weekly_avg = (total_sales * 7) / max(date_range_days, 1)    # Annualize to weekly
                daily_avg = total_sales / max(date_range_days, 1)
            else:
                monthly_avg = weekly_avg = daily_avg = 0
            
            top_product_card_content = html.Div(
                style={
                    "border": f"2px solid {theme['accent_dark_blue']}",
                    "borderRadius": "10px",
                    "padding": "16px",
                    "backgroundColor": theme["card_bg"],
                    "boxShadow": f"0 2px 6px rgba(0,0,0,0.2)",
                },
                children=[
                    html.H4(f"Top Product: {top_product_id}", style={"margin": "0 0 12px 0", "color": theme["text"], "fontWeight": "600"}),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr 1fr", "gap": "12px"},
                        children=[
                            html.Div(
                                style={
                                    "border": f"2px solid {theme['accent_green']}",
                                    "borderRadius": "8px",
                                    "padding": "10px",
                                    "backgroundColor": theme["card_bg"],
                                },
                                children=[
                                    html.Div("Total Gross Sales", style={"fontSize": "11px", "opacity": 0.75, "color": theme["text"], "fontWeight": "500"}),
                                    html.Div(f"${total_sales:,.2f}", style={"fontSize": "18px", "fontWeight": "bold", "marginTop": "4px", "color": theme["text"]}),
                                ],
                            ),
                            html.Div(
                                style={
                                    "border": f"2px solid {theme['accent_blue']}",
                                    "borderRadius": "8px",
                                    "padding": "10px",
                                    "backgroundColor": theme["card_bg"],
                                },
                                children=[
                                    html.Div("Monthly Avg", style={"fontSize": "11px", "opacity": 0.75, "color": theme["text"], "fontWeight": "500"}),
                                    html.Div(f"${monthly_avg:,.2f}", style={"fontSize": "18px", "fontWeight": "bold", "marginTop": "4px", "color": theme["text"]}),
                                ],
                            ),
                            html.Div(
                                style={
                                    "border": f"2px solid {theme['accent_green']}",
                                    "borderRadius": "8px",
                                    "padding": "10px",
                                    "backgroundColor": theme["card_bg"],
                                },
                                children=[
                                    html.Div("Weekly Avg", style={"fontSize": "11px", "opacity": 0.75, "color": theme["text"], "fontWeight": "500"}),
                                    html.Div(f"${weekly_avg:,.2f}", style={"fontSize": "18px", "fontWeight": "bold", "marginTop": "4px", "color": theme["text"]}),
                                ],
                            ),
                            html.Div(
                                style={
                                    "border": f"2px solid {theme['accent_blue']}",
                                    "borderRadius": "8px",
                                    "padding": "10px",
                                    "backgroundColor": theme["card_bg"],
                                },
                                children=[
                                    html.Div("Daily Avg", style={"fontSize": "11px", "opacity": 0.75, "color": theme["text"], "fontWeight": "500"}),
                                    html.Div(f"${daily_avg:,.2f}", style={"fontSize": "18px", "fontWeight": "bold", "marginTop": "4px", "color": theme["text"]}),
                                ],
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

    # Sales trend
    if "order_date" in dff.columns and dff["order_date"].notna().any():
        trend = (
            dff.assign(day=dff["order_date"].dt.to_period("D").dt.to_timestamp())
               .groupby("day", as_index=False)["total_sales"]
               .sum() if "total_sales" in dff.columns else
            dff.assign(day=dff["order_date"].dt.to_period("D").dt.to_timestamp())
               .assign(derived_sales=dff.get("quantity", 0).fillna(0) * dff.get("unit_price", 0).fillna(0))
               .groupby("day", as_index=False)["derived_sales"]
               .sum()
        )
        y_col = "total_sales" if "total_sales" in trend.columns else "derived_sales"
        chart_template = "plotly_dark" if current_theme == "dark" else "plotly"
        sales_trend_fig = px.line(trend, x="day", y=y_col, markers=True, title="Revenue Trend (Daily)", template=chart_template)
        sales_trend_fig.update_layout(hovermode="x unified")
    else:
        chart_template = "plotly_dark" if current_theme == "dark" else "plotly"
        sales_trend_fig = px.histogram(dff, x="total_sales" if "total_sales" in dff.columns else None, title="Sales", template=chart_template)

    # Category bar
    if "category" in dff.columns:
        cat = (
            dff.groupby("category", as_index=False)["total_sales"].sum()
            if "total_sales" in dff.columns
            else dff.assign(derived_sales=dff.get("quantity", 0).fillna(0) * dff.get("unit_price", 0).fillna(0))
                  .groupby("category", as_index=False)["derived_sales"].sum()
        )
        y_col = "total_sales" if "total_sales" in cat.columns else "derived_sales"
        chart_template = "plotly_dark" if current_theme == "dark" else "plotly"
        category_bar_fig = px.bar(cat.sort_values(y_col, ascending=False).head(12), x="category", y=y_col,
                                  title="Top Categories by Revenue", template=chart_template)
    else:
        chart_template = "plotly_dark" if current_theme == "dark" else "plotly"
        category_bar_fig = px.scatter(title="Category not found in dataset", template=chart_template)

    # Discount scatter
    chart_template = "plotly_dark" if current_theme == "dark" else "plotly"
    if all(c in dff.columns for c in ["discount", "total_sales"]):
        discount_scatter_fig = px.scatter(
            dff, x="discount", y="total_sales", title="Discount vs Total Sales",
            hover_data=[c for c in ["product_id", "category", "state"] if c in dff.columns],
            template=chart_template,
        )
    else:
        discount_scatter_fig = px.scatter(title="Discount vs Sales (columns missing)", template=chart_template)

    # Payment pie
    vibrant_colors = ["#2c7dd7", "#1bb083", "#1ca5b6", "#a9326c", "#7953de", "#f8d0b6", "#f2b992", "#1590a1", "#5165e1", "#236ac1"]
    chart_template = "plotly_dark" if current_theme == "dark" else "plotly"
    if "payment_method" in dff.columns:
        pay = dff["payment_method"].fillna("Unknown").astype(str).value_counts().reset_index()
        pay.columns = ["payment_method", "count"]
        payment_pie_fig = px.pie(pay, names="payment_method", values="count", title="Payment Method Mix", color_discrete_sequence=vibrant_colors, template=chart_template)
    else:
        payment_pie_fig = px.pie(names=["Unknown"], values=[1], title="Payment Method Mix (missing column)", color_discrete_sequence=vibrant_colors, template=chart_template)

    # Table
    show_cols = [c for c in [
        "order_id", "order_date", "customer_id", "state", "city",
        "product_id", "category", "sub_category", "brand",
        "quantity", "unit_price", "discount", "shipping_cost", "total_sales",
        "payment_method", "order_status"
    ] if c in dff.columns]

    table_df = dff[show_cols].copy() if show_cols else dff.head(50).copy()
    # Make datetimes display nicely
    for c in table_df.columns:
        if pd.api.types.is_datetime64_any_dtype(table_df[c]):
            table_df[c] = table_df[c].dt.strftime("%Y-%m-%d")

    columns = [{"name": c, "id": c} for c in table_df.columns]
    data = table_df.head(500).to_dict("records")

    return top_product_card_content, kpis, sales_trend_fig, category_bar_fig, discount_scatter_fig, payment_pie_fig, data, columns, date_hint


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run_server(host="0.0.0.0", port=port, debug=False)