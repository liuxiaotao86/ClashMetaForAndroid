————————————————————————————————————————————————
这是一个自动计算包名的仓库：
维护：
DirectApps.txt  手动将所有直连app的包名按照每行一个编辑
RejectApps.txt  手动将所有拦截app的包名按照每行一个编辑
SystemApps.txt  系统app
app-list.csv    这是由applist app提取的所有app的包名信息，此自动化格式固定csv

产出：
DirectApps.yaml
RejectApps.yaml
SystemApps.yaml
ProxyApps.txt
ProxyApps.yaml
PackageNames.json  直接由csv生成的包名-名称映射表，每次变动merge进去，包名作为唯一识别码。此json作为全部映射集合被调用

功能：
txt带去重包名排序后生成对应yaml
ProxyApps=AllApps-SystemApps-DirectApps-RejectApps

实际使用中，目前直接使用DirectApps和RejectApps其他全部proxy，并没有针对system和proxy apps在单独进行分流处理
后续看情况是否将部分yaml推送到gist，当前暂时使用jsdelivr的cdn分发解决偶发抽风无法直接获取GitHub资源问题
