import streamlit as st
import pandas as pd
import extra_streamlit_components as stx
import altair as alt

st.set_page_config(layout="wide")

@st.cache(allow_output_mutation=True)
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()
cookies = cookie_manager.get_all()
st.write(cookies)

st.title("Aggregate portfolio of ETFs and stocks")

# ETFs
etfs = pd.read_csv('data/blackrock_fr.csv')
previous_etfs = cookie_manager.get(cookie='etf_holdings')

if previous_etfs:
  etf_choices = st.multiselect("Select a fund", etfs.Fund.unique(), default=previous_etfs.keys())
else:
  etf_choices = st.multiselect("Select a fund", etfs.Fund.unique())

etf_holdings = {}
for etf in etf_choices:
  if etf in previous_etfs:
    etf_holdings[etf] = st.number_input(f'Total value of {etf} holding', min_value=0, step=10, value=previous_etfs[etf])
  else:
    etf_holdings[etf] = st.number_input(f'Total value of {etf} holding', min_value=0, step=10)

# Stocks
stocks = pd.read_csv('data/individual_positions.csv')
previous_stocks = cookie_manager.get(cookie='stock_holdings')

if previous_stocks:
  stock_choices = st.multiselect("Select a stock", stocks.Name.unique(), default=previous_stocks.keys())
else:
  stock_choices = st.multiselect("Select a stock", stocks.Name.unique())

stock_holdings = {}
for stock in stock_choices:
  if stock in previous_stocks:
    stock_holdings[stock] = st.number_input(f'Total value of {stock} holding', min_value=0, step=10, value=previous_stocks[stock])
  else:
    stock_holdings[stock] = st.number_input(f'Total value of {stock} holding', min_value=0, step=10)

clicked = st.button('Show results')
saved = st.button('Save holdings')

if clicked:
  portfolio = etfs[etfs.Fund.isin(etf_choices)].copy()
  # for etf, holding in zip(etf_choices, etf_holdings):
  for etf, holding in etf_holdings.items():
    st.text(f'{etf}: {holding}€')
    portfolio.loc[portfolio.Fund == etf, 'Value'] = portfolio.loc[portfolio.Fund == etf, 'Weight (%)'] * holding / 100
    
  stock_portfolio = stocks[stocks.Name.isin(stock_choices)]
  # for stock, holding in zip(stock_choices, stock_holdings):
  for stock, holding in stock_holdings.items():
    st.text(f'{stock}: {holding}€')
    stock_portfolio.loc[stock_portfolio.Name == stock, 'Value'] = holding
  
  portfolio = pd.concat([portfolio, stock_portfolio])
  portfolio = portfolio.drop(columns=['Fund'])
  portfolio = portfolio.groupby(['Ticker', 'Name', 'Sector', 'Asset Class', 'Location'], as_index=False).Value.sum()
  portfolio['Weight (%)'] = portfolio.Value.div(portfolio.Value.sum()) * 100                              
  portfolio['Weight (%)'] = portfolio['Weight (%)'].round(2)
  portfolio = portfolio.sort_values(by='Value', ascending=False)
  
  sectors = portfolio.groupby('Sector')[['Value', 'Weight (%)']].sum()
  regions = portfolio.groupby('Location')[['Value', 'Weight (%)']].sum()
  asset_classes = portfolio.groupby('Asset Class')[['Value', 'Weight (%)']].sum()

  col1, col2, col3 = st.columns(3)
  col1.metric(
    "Top 10 concentration",
    value=f"{portfolio.iloc[:10]['Weight (%)'].sum():.0f}%"
  )
  col2.metric(
    "Largest sector",
    value=f"{sectors['Weight (%)'].max():.0f}%",
    delta=sectors['Weight (%)'].idxmax(),
    delta_color='off'
  )
  col3.metric(
    "Largest region", 
    value=f"{regions['Weight (%)'].max():.0f}%",
    delta=regions['Weight (%)'].idxmax(),
    delta_color='off'
  )

  st.header('Sectors')
  c_sectors = alt.Chart(sectors.sort_values(by='Value').reset_index()).mark_bar().encode(
      x='Weight (%)',
      y=alt.Y('Sector', sort='-x'),
      tooltip=['Sector', 'Weight (%)', 'Value']
  )
  st.altair_chart(c_sectors, use_container_width=True)

  st.header('Asset Classes')
  c_asset_classes = alt.Chart(asset_classes.sort_values(by='Value').reset_index()).mark_bar().encode(
      x='Weight (%)',
      y='Asset Class',
      tooltip=['Asset Class', 'Weight (%)', 'Value']
  )
  st.altair_chart(c_asset_classes, use_container_width=True)

  st.header('Regions')
  c = alt.Chart(regions.sort_values(by='Value').reset_index()).mark_bar().encode(
      x='Weight (%)',
      y=alt.Y('Location', sort='-x'),
      tooltip=['Location', 'Weight (%)', 'Value']
  )
  st.altair_chart(c, use_container_width=True)
  
  st.header('Holdings')
  st.dataframe(portfolio)

if saved:
  cookie_manager.set('etf_holdings', etf_holdings, key='etf_hokdings')
  cookie_manager.set('stock_holdings', stock_holdings, key='stock_holdings')
    
