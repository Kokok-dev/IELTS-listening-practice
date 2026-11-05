"""Build the per-user installer using an explicitly supplied Inno Setup compiler."""
from pathlib import Path
import argparse
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--iscc', type=Path, required=True)
args = parser.parse_args()
translations = {
    'LanguageName': '简体中文', 'LanguageID': '$0804',
    'SetupAppTitle': '安装', 'SetupWindowTitle': '安装 - %1',
    'UninstallAppTitle': '卸载', 'UninstallAppFullTitle': '%1 卸载',
    'InformationTitle': '信息', 'ConfirmTitle': '确认', 'ErrorTitle': '错误',
    'ButtonBack': '< 上一步(&B)', 'ButtonNext': '下一步(&N) >',
    'ButtonInstall': '安装(&I)', 'ButtonOK': '确定', 'ButtonCancel': '取消',
    'ButtonFinish': '完成(&F)', 'ButtonBrowse': '浏览(&B)...',
    'WizardWelcome': '欢迎使用 [name] 安装向导',
    'WelcomeLabel1': '即将安装 [name/ver]',
    'WelcomeLabel2': '此向导将在您的计算机上安装 [name/ver]。%n%n建议先关闭其他应用程序，然后单击“下一步”继续。',
    'WizardSelectDir': '选择安装位置',
    'SelectDirDesc': '将 [name] 安装到哪个文件夹？',
    'SelectDirLabel3': '安装程序将把 [name] 安装到下列文件夹。',
    'SelectDirBrowseLabel': '单击“下一步”继续，或者单击“浏览”选择其他文件夹。',
    'WizardSelectTasks': '选择附加任务', 'SelectTasksDesc': '需要执行哪些附加任务？',
    'SelectTasksLabel2': '选择需要执行的附加任务，然后单击“下一步”。',
    'WizardReady': '准备安装', 'ReadyLabel1': '安装程序已准备好安装 [name]。',
    'ReadyLabel2a': '单击“安装”开始安装，或单击“上一步”检查设置。',
    'ReadyMemoDir': '安装位置：', 'ReadyMemoTasks': '附加任务：',
    'WizardInstalling': '正在安装', 'InstallingLabel': '正在安装 [name]，请稍候。',
    'StatusExtractFiles': '正在复制文件...',
    'WizardFinished': '[name] 安装完成',
    'FinishedHeadingLabel': '[name] 安装完成',
    'FinishedLabelNoIcons': '[name] 已安装到您的计算机。',
    'FinishedLabel': '[name] 已安装到您的计算机。可以通过创建的快捷方式启动程序。',
    'ClickFinish': '单击“完成”退出安装向导。',
}
source = (args.iscc.resolve().parent / 'Default.isl').read_text('utf-8-sig')
lines = []
for line in source.splitlines():
    key = line.split('=', 1)[0]
    lines.append(key + '=' + translations[key] if key in translations else line)
(ROOT / 'installer/ChineseSimplified.isl').write_text('\n'.join(lines) + '\n', 'utf-8-sig')
subprocess.run([str(args.iscc.resolve()), str(ROOT / 'installer/juting.iss')], check=True)
