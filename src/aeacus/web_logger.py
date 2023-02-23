import json
import os.path
import time

from aiohttp import web

from aeacus import RESULTS_PATH

routes = web.RouteTableDef()
log_file = os.path.join(RESULTS_PATH, 'ue.log')


@routes.post('/log')
async def log(request):
    data = await request.text()
    data = json.loads(data)
    print(f'Receive log: {data}')
    data = {'ts': int(time.time() * 1000), 'data': data}
    with open(log_file, 'a+') as f:
        f.write(f'{json.dumps(data)}\n')
    return web.json_response({'status': 'ok'})


@routes.get('/test')
async def test(request):
    return web.json_response({'status': 'ok'})


def main():
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, port=8085)


if __name__ == '__main__':
    main()
