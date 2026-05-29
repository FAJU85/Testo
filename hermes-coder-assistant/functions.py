import re
import inspect
import requests
import pandas as pd
import yfinance as yf
import concurrent.futures

from typing import List
from bs4 import BeautifulSoup
from utils import inference_logger
from langchain.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool

@tool
def code_interpreter(code_markdown: str) -> dict | str:
    """
    Execute the provided Python code string on the terminal using exec.

    The string should contain valid, executable and pure Python code in markdown syntax.
    Code should also import any required Python packages.

    Args:
        code_markdown (str): The Python code with markdown syntax to be executed.
            For example: ```python\n<code-string>\n```

    Returns:
        dict | str: A dictionary containing variables declared and values returned by function calls,
            or an error message if an exception occurred.

    Note:
        Use this function with caution, as executing arbitrary code can pose security risks.
    """
    try:
        # Extracting code from Markdown code block
        code_lines = code_markdown.split('\n')[1:-1]
        code_without_markdown = '\n'.join(code_lines)

        # Create a new namespace for code execution
        exec_namespace = {}

        # Execute the code in the new namespace
        exec(code_without_markdown, exec_namespace)

        # Collect variables and function call results
        result_dict = {}
        for name, value in exec_namespace.items():
            if callable(value):
                try:
                    result_dict[name] = value()
                except TypeError:
                    # If the function requires arguments, attempt to call it with arguments from the namespace
                    arg_names = inspect.getfullargspec(value).args
                    args = {arg_name: exec_namespace.get(arg_name) for arg_name in arg_names}
                    result_dict[name] = value(**args)
            elif not name.startswith('_'):  # Exclude variables starting with '_'
                result_dict[name] = value

        return result_dict

    except Exception as e:
        error_message = f"An error occurred: {e}"
        inference_logger.error(error_message)
        return error_message

@tool
def google_search_and_scrape(query: str) -> dict:
    """
    Performs a Google search for the given query, retrieves the top search result URLs,
    and scrapes the text content and table data from those pages in parallel.

    Args:
        query (str): The search query.
    Returns:
        list: A list of dictionaries containing the URL, text content, and table data for each scraped page.
    """
    num_results = 2
    url = 'https://www.google.com/search'
    params = {'q': query, 'num': num_results}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.3'}
    
    inference_logger.info(f"Performing google search with query: {query}\nplease wait...")
    response = requests.get(url, params=params, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    urls = [result.find('a')['href'] for result in soup.find_all('div', class_='tF2Cxc')]
    
    inference_logger.info(f"Scraping text from urls, please wait...") 
    [inference_logger.info(url) for url in urls]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(lambda url: (url, requests.get(url, headers=headers).text if isinstance(url, str) else None), url) for url in urls[:num_results] if isinstance(url, str)]
        results = []
        for future in concurrent.futures.as_completed(futures):
            url, html = future.result()
            soup = BeautifulSoup(html, 'html.parser')
            paragraphs = [p.text.strip() for p in soup.find_all('p') if p.text.strip()]
            text_content = ' '.join(paragraphs)
            text_content = re.sub(r'\s+', ' ', text_content)
            table_data = [[cell.get_text(strip=True) for cell in row.find_all('td')] for table in soup.find_all('table') for row in table.find_all('tr')]
            if text_content or table_data:
                results.append({'url': url, 'content': text_content, 'tables': table_data})
    return results

@tool
def get_current_stock_price(symbol: str) -> float:
  """
  Get the current stock price for a given symbol.

  Args:
    symbol (str): The stock symbol.

  Returns:
    float: The current stock price, or None if an error occurs.
  """
  try:
    stock = yf.Ticker(symbol)
    # Use "regularMarketPrice" for regular market hours, or "currentPrice" for pre/post market
    current_price = stock.info.get("regularMarketPrice", stock.info.get("currentPrice"))
    return current_price if current_price else None
  except Exception as e:
    print(f"Error fetching current price for {symbol}: {e}")
    return None

@tool
def get_stock_fundamentals(symbol: str) -> dict:
    """
    Get fundamental data for a given stock symbol using yfinance API.

    Args:
        symbol (str): The stock symbol.

    Returns:
        dict: A dictionary containing fundamental data.
            Keys:
                - 'symbol': The stock symbol.
                - 'company_name': The long name of the company.
                - 'sector': The sector to which the company belongs.
                - 'industry': The industry to which the company belongs.
                - 'market_cap': The market capitalization of the company.
                - 'pe_ratio': The forward price-to-earnings ratio.
                - 'pb_ratio': The price-to-book ratio.
                - 'dividend_yield': The dividend yield.
                - 'eps': The trailing earnings per share.
                - 'beta': The beta value of the stock.
                - '52_week_high': The 52-week high price of the stock.
                - '52_week_low': The 52-week low price of the stock.
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        fundamentals = {
            'symbol': symbol,
            'company_name': info.get('longName', ''),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'market_cap': info.get('marketCap', None),
            'pe_ratio': info.get('forwardPE', None),
            'pb_ratio': info.get('priceToBook', None),
            'dividend_yield': info.get('dividendYield', None),
            'eps': info.get('trailingEps', None),
            'beta': info.get('beta', None),
            '52_week_high': info.get('fiftyTwoWeekHigh', None),
            '52_week_low': info.get('fiftyTwoWeekLow', None)
        }
        return fundamentals
    except Exception as e:
        print(f"Error getting fundamentals for {symbol}: {e}")
        return {}

@tool
def get_financial_statements(symbol: str) -> dict:
    """
    Get financial statements for a given stock symbol.

    Args:
    symbol (str): The stock symbol.

    Returns:
    dict: Dictionary containing financial statements (income statement, balance sheet, cash flow statement).
    """
    try:
        stock = yf.Ticker(symbol)
        financials = stock.financials
        return financials
    except Exception as e:
        print(f"Error fetching financial statements for {symbol}: {e}")
        return {}

@tool
def get_key_financial_ratios(symbol: str) -> dict:
    """
    Get key financial ratios for a given stock symbol.

    Args:
    symbol (str): The stock symbol.

    Returns:
    dict: Dictionary containing key financial ratios.
    """
    try:
        stock = yf.Ticker(symbol)
        key_ratios = stock.info
        return key_ratios
    except Exception as e:
        print(f"Error fetching key financial ratios for {symbol}: {e}")
        return {}

@tool
def get_analyst_recommendations(symbol: str) -> pd.DataFrame:
    """
    Get analyst recommendations for a given stock symbol.

    Args:
    symbol (str): The stock symbol.

    Returns:
    pd.DataFrame: DataFrame containing analyst recommendations.
    """
    try:
        stock = yf.Ticker(symbol)
        recommendations = stock.recommendations
        return recommendations
    except Exception as e:
        print(f"Error fetching analyst recommendations for {symbol}: {e}")
        return pd.DataFrame()

@tool
def get_dividend_data(symbol: str) -> pd.DataFrame:
    """
    Get dividend data for a given stock symbol.

    Args:
    symbol (str): The stock symbol.

    Returns:
    pd.DataFrame: DataFrame containing dividend data.
    """
    try:
        stock = yf.Ticker(symbol)
        dividends = stock.dividends
        return dividends
    except Exception as e:
        print(f"Error fetching dividend data for {symbol}: {e}")
        return pd.DataFrame()

@tool
def get_company_news(symbol: str) -> pd.DataFrame:
    """
    Get company news and press releases for a given stock symbol.

    Args:
    symbol (str): The stock symbol.

    Returns:
    pd.DataFrame: DataFrame containing company news and press releases.
    """
    try:
        news = yf.Ticker(symbol).news
        return news
    except Exception as e:
        print(f"Error fetching company news for {symbol}: {e}")
        return pd.DataFrame()

@tool
def get_technical_indicators(symbol: str) -> pd.DataFrame:
    """
    Get technical indicators for a given stock symbol.

    Args:
    symbol (str): The stock symbol.

    Returns:
    pd.DataFrame: DataFrame containing technical indicators.
    """
    try:
        indicators = yf.Ticker(symbol).history(period="max")
        return indicators
    except Exception as e:
        print(f"Error fetching technical indicators for {symbol}: {e}")
        return pd.DataFrame()

@tool
def get_company_profile(symbol: str) -> dict:
    """
    Get company profile and overview for a given stock symbol.

    Args:
    symbol (str): The stock symbol.

    Returns:
    dict: Dictionary containing company profile and overview.
    """
    try:
        profile = yf.Ticker(symbol).info
        return profile
    except Exception as e:
        print(f"Error fetching company profile for {symbol}: {e}")
        return {}

def get_openai_tools() -> List[dict]:
    functions = [
        code_interpreter,
        google_search_and_scrape,
        get_current_stock_price,
        get_company_news,
        get_company_profile,
        get_stock_fundamentals,
        get_financial_statements,
        get_key_financial_ratios,
        get_analyst_recommendations,
        get_dividend_data,
        get_technical_indicators,
        get_weather,
        unit_converter,
        calculate,
    ]
    tools = [convert_to_openai_tool(f) for f in functions]
    return tools

@tool
def get_weather(city: str, country_code: str = "US") -> dict:
    """
    Get current weather for a city using Open-Meteo API (free, no API key).

    Args:
        city (str): Name of the city.
        country_code (str): Two-letter country code (default: US).

    Returns:
        dict: Weather information including temperature, conditions, humidity, wind speed.
    """
    try:
        # First geocode the city
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}
        geo_resp = requests.get(geo_url, params=geo_params)
        geo_data = geo_resp.json()
        
        if "results" not in geo_data or not geo_data["results"]:
            return {"error": f"City '{city}' not found"}
        
        location = geo_data["results"][0]
        lat, lon = location["latitude"], location["longitude"]
        
        # Get weather
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            "timezone": "auto"
        }
        weather_resp = requests.get(weather_url, params=weather_params)
        weather_data = weather_resp.json()
        
        current = weather_data.get("current", {})
        weather_code_map = {
            0: "Clear", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
            45: "Fog", 48: "Rime Fog", 51: "Light Drizzle", 53: "Drizzle",
            55: "Dense Drizzle", 61: "Light Rain", 63: "Rain", 65: "Heavy Rain",
            71: "Light Snow", 73: "Snow", 75: "Heavy Snow", 80: "Rain Showers",
            95: "Thunderstorm"
        }
        
        return {
            "city": city,
            "temperature_c": current.get("temperature_2m"),
            "temperature_f": round(current.get("temperature_2m", 0) * 9/5 + 32, 1),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "condition": weather_code_map.get(current.get("weather_code", 0), "Unknown"),
            "source": "Open-Meteo (free API)"
        }
    except Exception as e:
        return {"error": f"Weather fetch error: {str(e)}"}

@tool
def unit_converter(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert between common units of measurement.

    Supported conversions:
    - Length: km, m, cm, mm, mi, ft, in, yd
    - Weight: kg, g, lb, oz
    - Temperature: C, F, K
    - Volume: L, mL, gal, fl_oz

    Args:
        value (float): The value to convert.
        from_unit (str): Source unit.
        to_unit (str): Target unit.

    Returns:
        float: Converted value.
    """
    try:
        conversions = {
            # Length (base: meters)
            "km_m": 1000, "m_m": 1, "cm_m": 0.01, "mm_m": 0.001,
            "mi_m": 1609.344, "ft_m": 0.3048, "in_m": 0.0254, "yd_m": 0.9144,
            # Weight (base: kg)
            "kg_kg": 1, "g_kg": 0.001, "lb_kg": 0.453592, "oz_kg": 0.0283495,
        }
        
        from_unit = from_unit.lower().strip()
        to_unit = to_unit.lower().strip()
        key = f"{from_unit}_{to_unit}"
        
        # Temperature conversions
        if from_unit == "c" and to_unit == "f":
            return value * 9/5 + 32
        elif from_unit == "f" and to_unit == "c":
            return (value - 32) * 5/9
        elif from_unit == "c" and to_unit == "k":
            return value + 273.15
        elif from_unit == "k" and to_unit == "c":
            return value - 273.15
        elif from_unit == "f" and to_unit == "k":
            return (value - 32) * 5/9 + 273.15
        elif from_unit == "k" and to_unit == "f":
            return (value - 273.15) * 9/5 + 32
        
        # Standard conversions
        if key in conversions:
            base_value = value * conversions[key]
            reverse_key = f"{to_unit}_{from_unit}"
            if reverse_key in conversions:
                return round(base_value / conversions[reverse_key], 6)
            return base_value
        
        return {"error": f"Conversion from {from_unit} to {to_unit} not supported"}
    except Exception as e:
        return f"Conversion error: {str(e)}"

@tool
def calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression.

    Args:
        expression (str): Mathematical expression (e.g., "2+2", "sqrt(16)", "sin(pi/2)").

    Returns:
        str: Result of the calculation.
    """
    try:
        import math
        
        # Safe globals for eval
        safe_dict = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow, "int": int, "float": float,
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "sqrt": math.sqrt, "pi": math.pi, "e": math.e,
            "log": math.log, "log10": math.log10, "exp": math.exp,
            "degrees": math.degrees, "radians": math.radians,
        }
        
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        
        if isinstance(result, float):
            if result == int(result):
                return str(int(result))
            return f"{result:.6f}".rstrip('0').rstrip('.')
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"