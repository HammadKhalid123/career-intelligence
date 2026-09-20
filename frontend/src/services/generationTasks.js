import { useSyncExternalStore } from "react";

const tasks = new Map();
const subscribers = new Map();
const idleTask = { status: "idle", result: null, error: null, input: null };

function notify(task) {
  subscribers.get(task.key)?.forEach((listener) => listener());
}

export function startGeneration(key, input, request) {
  const current = tasks.get(key);
  if (current?.status === "loading") return current.promise;

  const task = {
    status: "loading",
    result: null,
    error: null,
    input,
    key,
    promise: null,
  };
  task.promise = Promise.resolve()
    .then(request)
    .then((result) => {
      const completed = { ...task, status: "success", result };
      tasks.set(key, completed);
      notify(completed);
      return result;
    })
    .catch((error) => {
      const failed = { ...task, status: "error", error };
      tasks.set(key, failed);
      notify(failed);
      throw error;
    });
  tasks.set(key, task);
  notify(task);
  return task.promise;
}

export function clearGeneration(key) {
  tasks.delete(key);
}

function subscribe(key, listener) {
  const listeners = subscribers.get(key) || new Set();
  listeners.add(listener);
  subscribers.set(key, listeners);
  return () => {
    listeners.delete(listener);
    if (!listeners.size) subscribers.delete(key);
  };
}

function snapshot(key) {
  return tasks.get(key) || idleTask;
}

export function useGenerationTask(key) {
  return useSyncExternalStore(
    (listener) => subscribe(key, listener),
    () => snapshot(key),
    () => idleTask,
  );
}
