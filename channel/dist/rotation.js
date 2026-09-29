// Each lap gives the selected topics room; longer topic queues take turns.
export function balancedRotation(stories, cycle = 0) {
  const groups = new Map();
  for (const story of stories) {
    if (!groups.has(story.topic)) groups.set(story.topic, []);
    groups.get(story.topic).push(story);
  }
  const cap = groups.size >= 3 ? 2 : Infinity;
  const queues = [...groups.values()].map(group => {
    const count = Math.min(group.length, cap);
    const offset = Number.isFinite(cap) ? (cycle * cap) % group.length : 0;
    return Array.from({length:count}, (_, i) => group[(offset + i) % group.length]);
  });
  const output = [];
  while (queues.some(queue => queue.length)) {
    for (const queue of queues) if (queue.length) output.push(queue.shift());
  }
  return output;
}
