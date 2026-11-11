const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const sandbox = { window: {}, document: { querySelector: () => null }, Intl, Date, Set, Map };
vm.runInNewContext(fs.readFileSync('apps/demo/statistics.js', 'utf8'), sandbox);
const { compute, quantile, wilson } = sandbox.window.SIGDAStatistics;
assert.equal(quantile([10, 0, 30, 20], .9), 27);
assert.equal(quantile([], .5), null);
assert.equal(wilson(0, 0), null);
const ci = wilson(5, 10);
assert(Math.abs(ci[0] - .23659) < .0001 && Math.abs(ci[1] - .76341) < .0001);
const now = Date.parse('2026-11-11T12:00:00+01:00'), hour = 3600000;
const result = compute({ now, records: [{
    events: [{ type: 'submit', status: 'submitted', at: now - 100 * hour },
        { type: 'return', status: 'draft', at: now - 90 * hour },
        { type: 'submit', status: 'submitted', at: now - 80 * hour },
        { type: 'approve', status: 'ap', at: now - 60 * hour },
        { type: 'approve', status: 'approved', at: now - 50 * hour }],
    tasks: [{ stage: 'SECAD', state: 'pending', createdAt: now - hour, dueAt: now - 1 }]
}], usage: [{ at: now - hour, actor: 'ops', action: 'login' },
    { at: now - 2 * hour, actor: 'ops', action: 'preview' },
    { at: now + hour, actor: 'future', action: 'login' }] }, 7);
assert.equal(result.submitted, 2);
assert.equal(result.approved, 1); // Intermediate approvals are not final decisions.
assert.equal(result.returned, 1);
assert.equal(result.durations[0], 50); // Corrections remain in the end-to-end delay.
assert.equal(result.active, 1);
assert.equal(result.usage.length, 2);
assert.equal(result.stages[1].overdue, 1);
assert.equal(result.days.length, 7);
assert.equal(result.days.reduce((n, d) => n + d.decided, 0), 1);
// Kinshasa midnight belongs to the new day even though UTC is still the previous day.
const boundary = compute({ now, records: [], usage: [{ at: Date.parse('2026-11-10T23:00:00Z'), actor: 'ops', action: 'login' }] }, 7);
assert.equal(boundary.days.at(-1).actions, 1);
console.log('Statistics: quantiles, Wilson interval, cohort, calendar boundary and actual-event counts passed.');
