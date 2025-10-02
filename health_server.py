from aiohttp import web
import threading

def start_health_server():
    """Starts a simple health check server on port 8000 in a separate thread."""
    
    async def health_check(request):
        """Handle health check requests."""
        return web.Response(text="OK", status=200)
    
    def run_server():
        app = web.Application()
        app.router.add_get('/', health_check)
        app.router.add_get('/health', health_check)
        web.run_app(app, host='0.0.0.0', port=8000, access_log=None)
    
    # Start the server in a daemon thread so it doesn't block the main program
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
