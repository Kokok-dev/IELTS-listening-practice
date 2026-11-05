"""句听 Windows desktop entry. --serve is also useful for browser development."""
import argparse
import ctypes
import logging
import os
from pathlib import Path
import socket
import sys
import threading
import time
import urllib.request


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--serve',action='store_true')
    parser.add_argument('--port',type=int,default=8877)
    parser.add_argument('--data-dir',type=Path)
    args=parser.parse_args()
    frozen=getattr(sys,'frozen',False)
    root=Path(sys.executable).parent if frozen else Path(__file__).parent
    assets=(Path(sys._MEIPASS) if frozen else root)/'web'
    data=args.data_dir or root/'data'
    data.mkdir(parents=True,exist_ok=True)
    instance_lock=None
    if os.name=='nt' and not args.serve:
        import msvcrt
        instance_lock=open(data/'.instance.lock','a+b')
        if instance_lock.seek(0,2)==0:
            instance_lock.write(b'0');instance_lock.flush()
        instance_lock.seek(0)
        try:
            msvcrt.locking(instance_lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:
            instance_lock.close()
            user32=ctypes.windll.user32
            existing=user32.FindWindowW(None,'句听 · IELTS 精听')
            if existing:
                user32.ShowWindow(existing,9)
                user32.SetForegroundWindow(existing)
            else:
                user32.MessageBoxW(0,'句听已在运行或正在保存任务，请稍后再试。','句听',0x40)
            return
    logging.basicConfig(filename=str(data/'juting.log'),level=logging.INFO,encoding='utf-8',
                        format='%(asctime)s %(levelname)s %(message)s')
    # Avoid hidden-console logging assumptions in Uvicorn/pythonnet.
    if sys.stdout is None:
        sys.stdout=open(data/'stdout.log','a',encoding='utf-8')
    if sys.stderr is None:
        sys.stderr=open(data/'stderr.log','a',encoding='utf-8')
    try:
        import uvicorn
        from juting.server import create_app
        app=create_app(data,root/'models'/'small.en',assets)
        with socket.socket() as probe:
            try:
                probe.bind(('127.0.0.1',args.port))
            except OSError:
                probe.bind(('127.0.0.1',0))
            port=probe.getsockname()[1]
        server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_config=None,access_log=False))
        if args.serve:
            print(f'JUTING_URL=http://127.0.0.1:{port}',flush=True)
            server.run()
            return
        server_thread=threading.Thread(target=server.run,daemon=True)
        server_thread.start()
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        url=f'http://127.0.0.1:{port}'
        for _ in range(120):
            try:
                opener.open(url+'/api/status',timeout=.5)
                break
            except Exception:
                time.sleep(.1)
        else:
            raise RuntimeError('本地服务启动超时，请查看 data/juting.log。')
        import webview
        webview.settings['ALLOW_DOWNLOADS']=True
        window=webview.create_window('句听 · IELTS 精听',url,width=1380,height=920,min_size=(1040,720),
                                     background_color='#F7F8FC',text_select=True)
        closing_pending=threading.Event()
        def finish_shutdown():
            # Keep the local API alive briefly for already-queued autosaves.
            # WebView2/.NET cleanup can otherwise leave a headless process after
            # minimization. Drain our own writes/jobs, then end this app only.
            time.sleep(.9)
            logging.info('Closing window: draining local service and jobs')
            server.should_exit=True
            server_thread.join(timeout=15)
            app.state.executor.shutdown(wait=True,cancel_futures=False)
            logging.info('Application data saved; exiting')
            logging.shutdown()
            os._exit(0)
        def closing():
            if not closing_pending.is_set():
                closing_pending.set()
                threading.Thread(target=finish_shutdown,daemon=False).start()
        window.events.closing+=closing
        webview.start(gui='edgechromium',private_mode=False,storage_path=str(data/'webview'))
        server.should_exit=True
    except Exception as exc:
        logging.exception('Application failed')
        if os.name=='nt':
            ctypes.windll.user32.MessageBoxW(0,f'启动失败：{exc}\n\n日志位置：{data / "juting.log"}\n如提示 WebView2，请安装 Microsoft Edge WebView2 Runtime。','句听',0x10)
        else:
            raise


if __name__=='__main__':
    main()
