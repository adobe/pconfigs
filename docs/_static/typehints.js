/*
  Heuristically mark Python type-hint identifiers inside Pygments-rendered code blocks.
  We look for spans of class "n" (generic names) that appear:
    - after ':' or '->' on the same visual line (annotation context)
    - before '=' or ',' or ')' or ':' terminators
  Then we add the class "typehint" to those spans so CSS can style them.

  This is a best-effort DOM-side enhancement; it doesn't change source.
*/
(function () {
  function isPythonBlock(pre) {
    // Sphinx puts code inside <div class="highlight-python notranslate"><div class="highlight"><pre>...
    var container = pre.closest('.highlight-python');
    return !!container;
  }

  function processPre(pre) {
    if (!isPythonBlock(pre)) return;
    // Walk lines by splitting on <span class="w">\n? but easier: iterate child nodes and track columns.
    // We'll do a simple pass: for each text node, scan chars; when encountering ':' or '->',
    // mark a flag until a line break that subsequent Name tokens are in annotation context.
    var walker = document.createTreeWalker(pre, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
    var inAnnotation = false;
    while (walker.nextNode()) {
      var node = walker.currentNode;
      if (node.nodeType === Node.TEXT_NODE) {
        var text = node.nodeValue;
        // Reset at newline occurrences within text nodes
        for (var i = 0; i < text.length; i++) {
          var ch = text[i];
          var next = text[i + 1] || '';
          if (ch === '\n') {
            inAnnotation = false;
            continue;
          }
          if (ch === ':' || (ch === '-' && next === '>')) {
            inAnnotation = true;
          }
          // If we hit an '=' before a comma/paren, stop annotation context.
          if (ch === '=' || ch === ';') {
            inAnnotation = false;
          }
        }
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        var el = node;
        // Newline resets often live in text nodes; still, reset on <br>
        if (el.tagName === 'BR') {
          inAnnotation = false;
          continue;
        }
        // Pygments generic name spans get class 'n'
        if (inAnnotation && el.classList && el.classList.contains('n')) {
          // Avoid marking obvious variables on left of ':' (we only mark after it)
          el.classList.add('typehint');
        }
        // Terminate context at delimiters encountered as separate tokens
        if (el.classList && (el.classList.contains('p') || el.classList.contains('o'))) {
          var t = el.textContent || '';
          if (t.includes(')') || t.includes(',') || t.includes(':')) {
            inAnnotation = false;
          }
        }
      }
    }
  }

  function run() {
    document.querySelectorAll('div.highlight pre').forEach(processPre);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }

  // Re-run after theme/content lazy loads (Furo swaps content on navigation)
  document.addEventListener('DOMContentLoaded', function () {
    setTimeout(run, 0);
  });
})();


