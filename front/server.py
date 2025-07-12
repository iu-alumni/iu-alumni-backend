import http.server
import socketserver
import os

# Порт для HTTP-сервера
PORT = 8000

# Обработчик запросов
Handler = http.server.SimpleHTTPRequestHandler

# Запуск сервера
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Сервер запущен на порту {PORT}")
    print(f"Откройте http://localhost:{PORT} в браузере")
    httpd.serve_forever()