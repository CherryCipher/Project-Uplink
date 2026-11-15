/**
 * Live leaderboards are optional. games.json remains the fallback for games
 * without a generated leaderboard, or when the generated file is unavailable.
 */
export async function loadLiveLeaderboards() {
  try {
    const response = await fetch('./leaderboards.json', { cache: 'no-store' });
    if (!response.ok) return null;
    const data = await response.json();
    return data && typeof data.games === 'object' && data.games !== null ? data.games : null;
  } catch {
    return null;
  }
}

/** Merge automatically generated results only for the three supported games. */
export function withLiveLeaderboard(game, allBoards) {
  if (!['xonotic', 'assaultcube', 'openarena'].includes(game.id)) return game;
  if (!allBoards || !Object.prototype.hasOwnProperty.call(allBoards, game.id)) return game;
  const board = allBoards[game.id];
  if (!board || !Array.isArray(board.players)) return game;
  return {
    ...game,
    leaderboard: board.players.filter(entry =>
      entry && typeof entry.name === 'string' &&
      Number.isFinite(entry.score)
    ).map(entry => ({ name: entry.name, score: entry.score })),
    leaderboardLabel: board.label || 'Frags',
    leaderboardLive: true,
    leaderboardUpdated: board.updated || null
  };
}
