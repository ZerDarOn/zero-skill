# 异步文档打开
Python 3.11+，仅标准库。DocumentController持有project/text/loading/error四个公开状态。open(project, loader)开始时选择项目，清空显示文字与错误并设置loading；loader接收project，异步返回文稿字符串。edit(text)记录用户当前输入，close()关闭当前项目并清空全部公开状态。
报告：A项目加载慢，切换到B后突然又显示A；加载时用户输入的文字也可能被覆盖。
契约：只有最新一次open请求可以提交结果、错误或结束loading，包括A→B→A重复选择同一项目的情况。等待期间的edit必须保留；当前请求成功或失败仍结束loading。当前请求失败时显示错误但保留已有用户编辑。close以后旧请求不能恢复内容或错误。取消open应向调用者传播CancelledError，仅当前请求的取消可结束loading。每次open开始清空文字的既有行为要保留。无需取消旧loader、增加网络请求、持久化或第三方依赖。
