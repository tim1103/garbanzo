// 全局工具函数
function toast(msg, type='info') {
    const t = document.getElementById('globalToast');
    const body = document.getElementById('toastBody');
    const title = document.getElementById('toastTitle');
    const colors = {info:'#2b6cb0', success:'#2f855a', error:'#c53030', warn:'#b7791f'};
    title.textContent = {info:'提示', success:'成功', error:'错误', warn:'警告'}[type] || '提示';
    body.textContent = msg;
    t.className = 'toast show';
    t.style.borderLeft = `4px solid ${colors[type]||'#2b6cb0'}`;
    setTimeout(()=>t.classList.remove('show'), 3000);
}

async function api(url, opts={}) {
    const r = await fetch(url, {
        headers: {'Content-Type':'application/json'},
        ...opts,
        body: opts.body ? JSON.stringify(opts.body) : undefined
    });
    if (!r.ok) {
        const err = await r.json().catch(()=>({msg:'请求失败'}));
        throw new Error(err.msg || `HTTP ${r.status}`);
    }
    return r.json();
}

// 题型字典
const Q_TYPE = {
    'single_choice':'单选题',
    'python_read':'Python阅读题',
    'python_fill':'Python代码填空题',
    'flowchart':'流程图分析题',
    'flask_fill':'Flask代码填空题',
    'pandas':'Pandas数据处理题',
    'binary_tree':'二叉树操作题',
    'linked_list':'链表操作题'
};

// 难度星星
function diffStars(d) {
    return '★'.repeat(d) + '☆'.repeat(5-d);
}

// HTML转义
function esc(s) {
    if (!s) return '';
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
            .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// 题干预览渲染（带语法高亮、MathJax、Mermaid）
function renderStemPreview(html, container) {
    if (!container) return;
    container.innerHTML = html || '';
    // 渲染Mermaid
    container.querySelectorAll('code.language-mermaid, .mermaid').forEach(el=>{
        try { mermaid.run({nodes:[el]}); } catch(e) {}
    });
    // 重新渲染MathJax
    if (window.MathJax) {
        MathJax.typesetPromise([container]).catch(()=>{});
    }
}

// LocalStorage 草稿自动保存（PRD: 每分钟自动保存）
class DraftAutoSave {
    constructor(key, collectFn, restoreFn) {
        this.key = key;
        this.collectFn = collectFn;
        this.restoreFn = restoreFn;
        this.timer = null;
        this.indicator = null;
        this._createIndicator();
    }
    _createIndicator() {
        this.indicator = document.createElement('div');
        this.indicator.className = 'draft-indicator';
        this.indicator.innerHTML = '<i class="bi bi-cloud-check"></i> 草稿已自动保存';
        document.body.appendChild(this.indicator);
    }
    start() {
        // 每分钟自动保存
        this.timer = setInterval(()=>this.save(), 60000);
        // 检查是否有未恢复草稿
        window.addEventListener('load', ()=>this._checkRestore());
    }
    save() {
        try {
            const data = this.collectFn();
            if (!data) return;
            localStorage.setItem(this.key, JSON.stringify({
                ts: Date.now(),
                data
            }));
            this.indicator.classList.add('show');
            setTimeout(()=>this.indicator.classList.remove('show'), 2000);
        } catch(e) { console.warn('Draft save failed', e); }
    }
    _checkRestore() {
        const raw = localStorage.getItem(this.key);
        if (!raw) return;
        try {
            const obj = JSON.parse(raw);
            // 显示恢复弹窗
            this._showRestoreModal(obj);
        } catch(e) {}
    }
    _showRestoreModal(stored) {
        const time = new Date(stored.ts).toLocaleString('zh-CN');
        const modal = document.createElement('div');
        modal.className = 'draft-modal show';
        modal.innerHTML = `
            <div class="modal-box">
                <h5><i class="bi bi-exclamation-triangle text-warning"></i> 发现未保存的草稿</h5>
                <p class="text-muted">检测到 ${time} 自动保存的草稿，是否恢复？</p>
                <div class="d-flex justify-content-end gap-2 mt-3">
                    <button class="btn btn-secondary" id="discardDraft">放弃</button>
                    <button class="btn btn-primary" id="restoreDraft">恢复草稿</button>
                </div>
            </div>`;
        document.body.appendChild(modal);
        modal.querySelector('#restoreDraft').onclick = ()=>{
            this.restoreFn(stored.data);
            modal.remove();
        };
        modal.querySelector('#discardDraft').onclick = ()=>{
            localStorage.removeItem(this.key);
            modal.remove();
        };
    }
    clear() {
        localStorage.removeItem(this.key);
    }
}

// 全局快捷键 - PRD: Tab跳转填空、Esc关闭弹窗、Ctrl+Enter保存
function setupGlobalShortcuts() {
    document.addEventListener('keydown', (e)=>{
        // Esc 关闭弹窗
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.show').forEach(m=>{
                bootstrap.Modal.getOrCreateInstance(m).hide();
            });
            document.querySelectorAll('.draft-modal.show').forEach(m=>m.remove());
        }
        // Ctrl+Enter 保存（在表单内）
        if ((e.ctrlKey||e.metaKey) && e.key === 'Enter') {
            const saveBtn = document.querySelector('[data-shortcut="save"]');
            if (saveBtn) {
                e.preventDefault();
                saveBtn.click();
            }
        }
    });
}
document.addEventListener('DOMContentLoaded', setupGlobalShortcuts);
