window.MathJax = {
  tex: {
    // 全书使用 $…$ / $$…$$ 定界符（arithmatex generic 模式保留原样包裹）。
    inlineMath: [["$", "$"], ["\\(", "\\)"]],
    displayMath: [["$$", "$$"], ["\\[", "\\]"]],
    processEscapes: true
  },
  options: {
    processHtmlClass: "arithmatex"
  }
};

document$.subscribe(() => {
  MathJax.typesetPromise();
});
