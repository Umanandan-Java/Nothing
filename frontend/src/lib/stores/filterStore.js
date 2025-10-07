// src/lib/stores/filterStore.js
import { writable, derived } from 'svelte/store';

const HIERARCHY = ['industry', 'section', 'state', 'action', 'sentiment'];

const createFilterStore = () => {
  const { subscribe, set, update } = writable({
    state: null,
    section: null,    // will store section_id (stable)
    action: null,
    sentiment: null,
    industry: null,
    drillDownPath: [] // e.g., ['industry','section']
  });

  function clearChildren(filtersObj, parentFilterType) {
    const idx = HIERARCHY.indexOf(parentFilterType);
    if (idx === -1) return filtersObj;
    const newFilters = { ...filtersObj };
    HIERARCHY.slice(idx + 1).forEach(ft => {
      newFilters[ft] = null;
    });
    // Trim drill path to parent index
    newFilters.drillDownPath = (newFilters.drillDownPath || []).filter(f => HIERARCHY.indexOf(f) <= idx);
    return newFilters;
  }

  return {
    subscribe,
    setFilter: (filterType, value) => {
      // backward-compatible, simple set
      update(filters => {
        if (filters[filterType] === value) {
          const newPath = filters.drillDownPath.filter(f => f !== filterType);
          return { ...filters, [filterType]: null, drillDownPath: newPath };
        }
        const newPath = filters.drillDownPath.includes(filterType) ? filters.drillDownPath : [...filters.drillDownPath, filterType];
        // clear children of this filter when user sets it (prevents stale deeper filters)
        let next = { ...filters, [filterType]: value, drillDownPath: newPath };
        next = clearChildren(next, filterType);
        return next;
      });
    },

    // More explicit drill-down / hierarchical set
    setDrillDownFilter: (filterType, value, parentFilterType = null) => {
      update(filters => {

        // Toggle: same value clicked -> clear
        if (filters[filterType] === value) {
          const newPath = filters.drillDownPath.filter(f => f !== filterType);
          // Also clear children of this filter (if any)
          let cleared = { ...filters, [filterType]: null, drillDownPath: newPath };
          cleared = clearChildren(cleared, filterType);
          return cleared;
        }

        // Build new state: clear any children deeper than this filter
        let next = { ...filters, [filterType]: value };
        next = clearChildren(next, filterType);

        // Build drill path: keep everything up to this filter, then add it
        const desiredIndex = HIERARCHY.indexOf(filterType);
        let newPath = (filters.drillDownPath || []).filter(f => HIERARCHY.indexOf(f) < desiredIndex);
        if (!newPath.includes(filterType)) newPath.push(filterType);
        next.drillDownPath = newPath;

        // If parentFilterType provided, ensure parent exists (no-op if not)
        if (parentFilterType) {
          const parentIdx = HIERARCHY.indexOf(parentFilterType);
          if (parentIdx !== -1) {
            // keep only up to parent in path, then add this filter
            newPath = newPath.filter(f => HIERARCHY.indexOf(f) <= parentIdx);
            if (!newPath.includes(parentFilterType)) newPath.push(parentFilterType);
            if (!newPath.includes(filterType)) newPath.push(filterType);
            next.drillDownPath = newPath;
          }
        }

        return next;
      });
    },

    clearFilter: (filterType) => {
      update(filters => {
        // Clear given filter and children of that filter
        let next = { ...filters, [filterType]: null };
        next = clearChildren(next, filterType);
        next.drillDownPath = (next.drillDownPath || []).filter(f => f !== filterType);
        return next;
      });
    },

    clearAllFilters: () => {
      set({
        state: null,
        section: null,
        action: null,
        sentiment: null,
        industry: null,
        drillDownPath: []
      });
    },

    reset: () => {
      set({
        state: null,
        section: null,
        action: null,
        sentiment: null,
        industry: null,
        drillDownPath: []
      });
    },

    // optional convenience to move one level up
    drillUp: () => {
      update(filters => {
        const path = (filters.drillDownPath || []);
        if (!path.length) return filters;
        const last = path[path.length - 1];
        const newFilters = { ...filters, [last]: null, drillDownPath: path.slice(0, -1) };
        // also clear children of new last if any
        if (newFilters.drillDownPath.length) {
          const newLast = newFilters.drillDownPath[newFilters.drillDownPath.length - 1];
          return clearChildren(newFilters, newLast);
        }
        return newFilters;
      });
    }
  };
};

export const filterStore = createFilterStore();

export const activeFilterCount = derived(
  filterStore,
  $filters => Object.entries($filters)
    .filter(([key, value]) => key !== 'drillDownPath' && value !== null)
    .length
);
