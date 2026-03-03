from __future__ import annotations

import os
import pandas as pd

import dash
from dash import Dash, dcc, html, Input, Output

import data_store
from theme import get_theme, LIGHT_THEME, DARK_THEME


DATA_PATH = os.path.join("dataset", "amazon_sales_dataset.csv")


def load_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"CSV not found at: {path}\n"
            f"Expected it at: dataset/amazon_sales_dataset.csv"
        )

    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]

    for col in ["order_date", "ship_date", "delivery_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in ["quantity", "unit_price", "discount", "shipping_cost", "total_sales"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def safe_unique_sorted(df: pd.DataFrame, col: str) -> list[str]:
    if col not in df.columns:
        return []
    vals = df[col].dropna().astype(str).unique().tolist()
    return sorted(vals)


# --- Load once in the shell ---
df_all = load_data(DATA_PATH)
data_store.df_all = df_all

# Default date bounds
if "order_date" in df_all.columns and df_all["order_date"].notna().any():
    min_date = df_all["order_date"].min().date()
    max_date = df_all["order_date"].max().date()
else:
    min_date, max_date = None, None

# Dropdown options
category_options = safe_unique_sorted(df_all, "category")
state_options = safe_unique_sorted(df_all, "state")
sub_category_options = safe_unique_sorted(df_all, "sub_category")

# --- Dash Pages app ---
dash_app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
server = dash_app.server
dash_app.title = "Amazon Sales Dashboard"

light_theme = get_theme("light")

dash_app.layout = html.Div(
    id="main-container",
    style={
        "minHeight": "100vh",
        "backgroundColor": light_theme["bg"],
        "color": light_theme["text"],
        "fontFamily": "Arial",
        "transition": "background-color 0.3s, color 0.3s",
    },
    children=[
        dcc.Store(id="theme-store", data="light", storage_type="local"),

        html.Div(
            style={"maxWidth": "1200px", "margin": "18px auto", "position": "relative"},
            children=[
                # Header / nav
                html.Div(
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "marginBottom": "18px",
                    },
                    children=[
                        html.H2("Amazon E-commerce Sales — Dash App", style={"margin": "0"}),
                        html.Div(
                            id="nav-box",
                            style={"display": "flex", "gap": "10px", "alignItems": "center"},
                            children=[
                                html.H2("Change View:", style={"margin": "0", "fontSize": "16px", "fontWeight": "600"}),
                                dcc.Link(
                                    "Overview",
                                    href="/",
                                    id="link-overview",
                                    style={"padding": "6px 10px", "border": "1px solid #999", "borderRadius": "6px"},
                                ),
                                dcc.Link(
                                    "Discount/Profit Outliers",
                                    href="/profit",
                                    id="link-profit",
                                    style={"padding": "6px 10px", "border": "1px solid #999", "borderRadius": "6px"},
                                ),
                                html.Button(
                                    "🌙 Dark Mode",
                                    id="theme-toggle-btn",
                                    n_clicks=0,
                                    style={
                                        "padding": "8px 16px",
                                        "borderRadius": "6px",
                                        "border": f"2px solid {light_theme['accent_blue']}",
                                        "backgroundColor": light_theme["card_bg"],
                                        "color": light_theme["text"],
                                        "fontSize": "12px",
                                        "fontWeight": "600",
                                        "cursor": "pointer",
                                        "transition": "all 0.3s",
                                    },
                                ),
                            ],
                        ),
                    ],
                ),

                # Shared slicers
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
                                    persistence=True,
                                    persistence_type="local",
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
                                    persistence=True,
                                    persistence_type="local",
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
                                    persistence=True,
                                    persistence_type="local",
                                ),
                            ]
                        ),
                    ],
                ),

                html.Div(style={"height": "10px"}),

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
                            persistence=True,
                            persistence_type="local",
                        ),
                        html.Div(
                            id="date_hint",
                            style={"fontSize": "12px", "opacity": 0.7, "marginTop": "6px"},
                        ),
                    ]
                ),

                html.Hr(),

                # Where Pages renders the current page
                dash.page_container,
            ],
        ),
    ],
)


@dash_app.callback(
    Output("theme-store", "data"),
    Output("theme-toggle-btn", "children"),
    Output("theme-toggle-btn", "style"),
    Output("main-container", "style"),
    Input("theme-toggle-btn", "n_clicks"),
    Input("theme-store", "data"),
)
def toggle_theme(n_clicks, current_theme):
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


@dash_app.callback(
    Output("category", "style"),
    Output("state", "style"),
    Output("sub_category", "style"),
    Output("date_range", "style"),
    Output("link-overview", "style"),
    Output("link-profit", "style"),
    Output("nav-box", "style"),
    Input("theme-store", "data"),
)
def update_dropdown_styles(current_theme):
    theme = get_theme(current_theme)
    dropdown_bg = theme["card_bg"]
    text_color = theme["text"]
    style = {
        "backgroundColor": dropdown_bg,
        "color": text_color,
        "border": f"1px solid {theme['border']}",
        "borderRadius": "6px",
        "padding": "6px",
    }
    date_style = {"backgroundColor": dropdown_bg, "color": text_color}
    link_style = {
        "padding": "6px 10px",
        "border": f"1px solid {theme['card_border']}",
        "borderRadius": "6px",
        "backgroundColor": "#f8d0b6" if current_theme == "dark" else "#e68b25",
        "color": "#000000",
        "textDecoration": "none",
        "display": "inline-block",
        "boxShadow": "0 6px 18px rgba(0,0,0,0.45)" if current_theme == "dark" else "0 6px 18px rgba(0,0,0,0.08)",
    }
    nav_box_bg = "transparent"
    nav_box_style = {
        "display": "flex",
        "gap": "10px",
        "alignItems": "center",
        "padding": "8px 12px",
        "borderRadius": "8px",
        "backgroundColor": nav_box_bg,
    }
    return style, style, style, date_style, link_style, link_style, nav_box_style


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    dash_app.run(host="0.0.0.0", port=port, debug=False)