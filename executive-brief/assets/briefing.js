/* Demonstration interactions; replace sample values with verified dated data. */
(() => {
  const charts = [];
  const chart = (id, option) => {
    if (!window.echarts) return null;
    const instance = echarts.init(document.getElementById(id), null, { renderer: 'svg' });
    instance.setOption({ animation: !matchMedia('(prefers-reduced-motion: reduce)').matches,
      textStyle: { fontSize: 18, fontFamily: 'Arial' },
      tooltip: { trigger: 'item', confine: true, textStyle: { fontSize: 18 } }, ...option });
    charts.push(instance);
    return instance;
  };
  chart('capacity', { grid: { left: 110, right: 45, top: 25, bottom: 65 },
    xAxis: { type: 'value', name: 'vCPU', nameLocation: 'middle', nameGap: 35, nameTextStyle: { fontSize: 18 }, axisLabel: { fontSize: 18 } },
    yAxis: { type: 'category', data: ['Baseline', 'Candidate'], axisLabel: { fontSize: 18 } },
    series: [{ type: 'bar', data: [2, 16], color: '#174f43', label: { show: true, position: 'right', fontSize: 18 } }] });
  chart('acceptance-chart', { legend: { bottom: 0, textStyle: { fontSize: 18 } },
    series: [{ type: 'pie', radius: ['35%', '65%'], center: ['50%', '43%'], label: { show: false },
      data: [{ name: 'Passed', value: 8, itemStyle: { color: '#174f43' } }, { name: 'Pending', value: 2, itemStyle: { color: '#9c782d' } }, { name: 'Failed', value: 1, itemStyle: { color: '#b34329' } }] }] });
  const cost = chart('cost-chart', { legend: { bottom: 0, textStyle: { fontSize: 18 } },
    series: [{ type: 'pie', radius: ['35%', '65%'], center: ['50%', '43%'], label: { show: false }, data: [] }] });
  const money = n => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);
  const refresh = () => {
    const value = id => Math.max(0, Number(document.getElementById(id).value) || 0);
    const data = [{ name: 'Compute', value: value('hourly') * value('hours') }, { name: 'Storage', value: value('storage') }, { name: 'Usage', value: value('usage') }];
    document.getElementById('cost-total').textContent = money(data.reduce((sum, row) => sum + row.value, 0));
    document.getElementById('cost-data').textContent = data.map(row => `${row.name}: ${money(row.value)}`).join(' · ');
    cost?.setOption({ series: [{ data }] });
  };
  ['hourly', 'hours', 'storage', 'usage'].forEach(id => document.getElementById(id).addEventListener('input', refresh));
  refresh();
  const nodes = {
    edge: ['DNS, TLS and edge', 'Resolves the domain, terminates TLS and routes allowed requests.', 'Verify DNS, certificate names/expiry, origin restrictions and cache behavior.'],
    artifacts: ['Artifacts and CDN', 'Stores and serves versioned outputs across a separate delivery boundary.', 'Verify object access, immutable paths, signed downloads and lifecycle retention.'],
    app: ['Web application', 'Authenticates users, validates submissions and serves the product.', 'Verify deployed revision, routes, authorization and live browser behavior.'],
    data: ['Database and cache', 'Keeps durable records and supports transient coordination.', 'Verify connectivity, backup restore, queue retry windows and lock semantics.'],
    worker: ['Queue workers', 'Processes isolated long-running jobs with bounded resources.', 'Verify concurrency, checkpoints, resource limits and graceful maintenance.'],
    provider: ['AI provider', 'Supplies generation and tool execution capacity.', 'Verify model, effort, skills, availability and budget separately from local compute.'],
    mail: ['Transactional email', 'Notifies owners and customers through the approved messaging flow.', 'Verify domain authentication, actual delivery, suppression and attribution.'],
    payment: ['Payments and delivery', 'Confirms payment before authorizing access to purchased files.', 'Verify webhook signatures, idempotency, refund handling and download gates.']
  };
  document.querySelectorAll('[data-node]').forEach(button => {
    button.setAttribute('aria-pressed', 'false');
    button.addEventListener('click', () => {
      document.querySelectorAll('[data-node]').forEach(node => node.setAttribute('aria-pressed', String(node === button)));
      const [title, detail, proof] = nodes[button.dataset.node];
      document.getElementById('node-title').textContent = title;
      document.getElementById('node-detail').textContent = detail;
      document.getElementById('node-proof').textContent = proof;
    });
  });
  new ResizeObserver(() => charts.forEach(instance => instance.resize())).observe(document.body);
  document.getElementById('print').addEventListener('click', () => window.print());
  document.getElementById('download').addEventListener('click', () => {
    const blob = new Blob(['<!doctype html>\n' + document.documentElement.outerHTML], { type: 'text/html' });
    const url = URL.createObjectURL(blob), anchor = document.createElement('a');
    anchor.href = url; anchor.download = 'executive-brief.html'; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
})();
