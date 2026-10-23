const $ = (selector) => document.querySelector(selector);
const quoteText = $('#quote-text');
const quoteAuthor = $('#quote-author');
const historyList = $('#history-list');
const newQuoteButton = $('#new-quote-btn');
const quoteStatus = $('#quote-status');
const toast = $('#toast');
let currentQuote = { quote: quoteText.textContent, author: quoteAuthor.textContent.replace(/^—\s*/, '') };
let toastTimer;

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2400);
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));
}
function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Just now';
  return date.toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}
function updateCounts(count) {
  $('#total-count').textContent = count;
  $('#history-count').textContent = count;
  $('#side-count').textContent = count;
}
async function loadHistory() {
  try {
    const response = await fetch('/api/history?limit=50');
    if (!response.ok) throw new Error('Could not load history');
    const entries = await response.json();
    updateCounts(entries.length);
    if (!entries.length) {
      historyList.innerHTML = '<div class="empty-state"><div class="empty-icon">◷</div><h3>Your story starts here</h3><p>Generate your first quote and it will appear in this collection.</p></div>';
      return;
    }
    historyList.innerHTML = entries.map((item, index) => `
      <article class="history-item">
        <div class="history-item-top"><span class="history-number">QUOTE ${String(entries.length - index).padStart(2, '0')}</span><span class="history-source">${item.source === 'api' ? 'API quote' : 'Offline quote'}</span></div>
        <p class="history-quote">“${escapeHtml(item.quote)}”</p>
        <div class="history-author">— ${escapeHtml(item.author)}</div>
        <div class="history-meta"><span>${escapeHtml(formatDate(item.created_at))}</span><button class="history-copy" data-copy-id="${item.id}" aria-label="Copy this quote">Copy quote ↗</button></div>
      </article>`).join('');
  } catch (error) {
    showToast('Could not load history. Check that the server is running.');
  }
}
async function generateQuote() {
  newQuoteButton.disabled = true;
  newQuoteButton.innerHTML = '<span class="refresh-icon">↻</span> Finding a quote…';
  quoteStatus.textContent = 'Connecting to quote service';
  try {
    const response = await fetch('/api/quotes/random', { method: 'POST' });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Could not generate a quote');
    currentQuote = result;
    quoteText.textContent = result.quote;
    quoteAuthor.textContent = `— ${result.author}`;
    quoteStatus.textContent = result.source === 'api' ? 'Fresh quote fetched and saved' : 'Offline quote saved';
    if (result.source !== 'api') showToast('Quote service unavailable; used a saved offline fallback.');
    await loadHistory();
  } catch (error) {
    quoteStatus.textContent = 'Could not generate quote';
    showToast(error.message || 'Something went wrong. Try again.');
  } finally {
    newQuoteButton.disabled = false;
    newQuoteButton.innerHTML = '<span class="refresh-icon">↻</span> Generate new quote';
  }
}
async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    showToast('Quote copied to clipboard.');
  } catch {
    const input = document.createElement('textarea');
    input.value = text; document.body.appendChild(input); input.select();
    const success = document.execCommand('copy'); input.remove();
    showToast(success ? 'Quote copied to clipboard.' : 'Copy failed. Select the quote and copy it manually.');
  }
}
newQuoteButton.addEventListener('click', generateQuote);
$('#copy-btn').addEventListener('click', () => copyText(`“${currentQuote.quote}” — ${currentQuote.author}`));
$('#clear-history-btn').addEventListener('click', async () => {
  const count = Number($('#history-count').textContent);
  if (!count) { showToast('Your history is already empty.'); return; }
  if (!window.confirm('Clear all saved quote history? This cannot be undone.')) return;
  try {
    const response = await fetch('/api/history', { method: 'DELETE' });
    if (!response.ok) throw new Error('Could not clear history');
    await loadHistory();
    showToast('Quote history cleared.');
  } catch (error) { showToast(error.message); }
});
historyList.addEventListener('click', (event) => {
  const button = event.target.closest('[data-copy-id]');
  if (!button) return;
  const card = button.closest('.history-item');
  const quote = card.querySelector('.history-quote').textContent;
  const author = card.querySelector('.history-author').textContent;
  copyText(`${quote} ${author}`);
});
loadHistory();
