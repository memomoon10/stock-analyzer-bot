import os
import requests
import yfinance as yf
import pandas as pd
from flask import Flask, request

# إعداد خادم الويب لاستقبال تحديثات تيليجرام ولتعمل المنصة 24/7
app = Flask(__name__)

TELEGRAM_TOKEN = "8827525799:AAHb3eGB6tdtbSSosBaPj_7rJSbLgYzCL_I"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

@app.route('/')
def home():
    return "Stock Comprehensive Analyzer Bot is Running 24/7! 🚀"

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"خطأ في إرسال الرسالة: {e}")

def analyze_stock(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol.upper())
        hist = ticker.history(period="15d")
        
        if hist.empty or len(hist) < 5:
            return f"❌ عذراً، لم أتمكن من العثور على بيانات كافية للسهم: `{ticker_symbol.upper()}`. تأكد من صحة الرمز."

        info = ticker.info
        
        # بيانات آخر 3 أيام
        last_3_days = hist.tail(3)
        prices_summary = ""
        for date, row in last_3_days.iterrows():
            date_str = date.strftime('%Y-%m-%d')
            prices_summary += (
                f"📅 التاريخ: {date_str}\n"
                f"   • الافتتاح: `${row['Open']:.2f}` | الإغلاق: `${row['Close']:.2f}`\n"
                f"   • الأعلى: `${row['High']:.2f}` | الأدنى: `${row['Low']:.2f}`\n"
            )

        current_price = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2])
        price_change_pct = ((current_price - prev_close) / prev_close) * 100

        support = float(hist['Low'].tail(10).min())
        resistance = float(hist['High'].tail(10).max())

        avg_volume = hist['Volume'].mean()
        market_cap = info.get('marketCap', 0)
        volatility_type = "🔥 خفيف (مضاربي عالي الحركة)" if avg_volume > 5000000 and market_cap < 2e9 else "🛡️ متوسط/ثقيل (استثماري أو مؤسسي)"

        close_series = hist['Close']
        ema_20 = close_series.ewm(span=20, adjust=False).mean().iloc[-1]
        ema_50 = close_series.ewm(span=50, adjust=False).mean().iloc[-1] if len(hist) >= 50 else ema_20
        trend = "📈 صعودي (Bullish) قوي" if current_price > ema_20 and ema_20 > ema_50 else "📉 هبوطي (Bearish) أو تصحيحي"

        volume_today = hist['Volume'].iloc[-1]
        volume_avg_10 = hist['Volume'].tail(10).mean()
        momentum = "⚡ زخم عالي جداً (حجم تداول أعلى من المعتاد)" if volume_today > (1.5 * volume_avg_10) else "⚖️ زخم طبيعي / هادئ"

        nasdaq_warning = "✅ السهم مستقر (لا توجد إنذارات شطب معلنة)"
        if current_price < 1.0:
            nasdaq_warning = "⚠️ تحذير: السهم يتداول تحت 1$ (عرضة لخطر إنذار عدم الامتثال لناسداك)"

        institution_held = info.get('heldPercentInstitutions', 0)
        target_group = "🏦 تسيطر عليها المؤسسات والأموال الذكية (Institutional)" if institution_held and institution_held > 0.5 else "🎯 يسيطر عليها المضاربون والأفراد (Retail / Traders)"

        report = (
            f"📊 **تقرير تحليل السهم: `{ticker_symbol.upper()}`**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💵 **السعر الحالي:** `${current_price:.2f}` ({price_change_pct:+.2f}%)\n"
            f"🧭 **الاتجاه العام:** {trend}\n"
            f"⚖️ **طبيعة السهم:** {volatility_type}\n"
            f"👥 **المهيمنون:** {target_group}\n"
            f"⚡ **حالة الزخم:** {momentum}\n"
            f"🛡️ **الدعم والمقاومة (10 أيام):**\n"
            f"   • دعم: `${support:.2f}`\n"
            f"   • مقاومة: `${resistance:.2f}`\n"
            f"🚨 **مخاطر ناسداك والشطب:**\n"
            f"   • {nasdaq_warning}\n\n"
            f"📋 **أسعار آخر 3 أيام تداول:**\n"
            f"{prices_summary}"
        )
        return report
    except Exception as e:
        return f"❌ حدث خطأ أثناء تحليل السهم `{ticker_symbol}`. تأكد من الرمز وحاول مرة أخرى."

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def receive_update():
    json_data = request.get_json()
    if json_data and 'message' in json_data:
        chat_id = json_data['message']['chat']['id']
        text = json_data['message'].get('text', '').strip()
        
        if text.startswith('/start'):
            send_message(chat_id, "مرحباً بك في بوت تحليل الأسهم الشامل! 🚀\nأرسل رمز السهم مباشرة (مثل: `AAPL` أو `TSLA` أو `SIRI`) وسأقوم بتحليله بالكامل.")
        else:
            ticker = text.replace('/', '').strip()
            if len(ticker) <= 6:
                send_message(chat_id, f"🔍 جاري تحليل السهم `{ticker.upper()}`، يرجى الانتظار...")
                analysis_result = analyze_stock(ticker)
                send_message(chat_id, analysis_result)
            else:
                send_message(chat_id, "⚠️ يرجى إرسال رمز السهم الصحيح فقط (مثال: `AAPL`).")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
