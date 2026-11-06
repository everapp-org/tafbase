---
id: CONCEPT-java-v1-010-01-sequenced-collections
status: accepted
subproject: java
layer: L2-language
since: Java 21
standing: recommended
---

# Sequenced Collections

## Definition

Sequenced collections (`SequencedCollection<E>`, `SequencedSet<E>`, `SequencedMap<K, V>`) unify collection types that possess a defined encounter order, providing uniform methods to access first/last elements and obtain reversed views.

```java
SequencedCollection<String> items = new ArrayList<>();
items.addFirst("head");
items.addLast("tail");

String first = items.getFirst();
String last = items.getLast();

for (String item : items.reversed()) {
    System.out.println(item);
}

SequencedMap<String, Integer> map = new LinkedHashMap<>();
map.putFirst("root", 0);
Map.Entry<String, Integer> oldest = map.firstEntry();
```

## Why it exists

Collections previously had no common supertype for ordered collections. Accessing the first or last element required disparate, clunky APIs: `list.get(0)` vs `iterator.next()`, `list.get(list.size() - 1)` vs `deque.getLast()` vs `sortedSet.last()`. Reversing iteration often required awkward indexing or full defensive copying. Sequenced collections bridge `List`, `Deque`, `LinkedHashSet`, and `SortedSet` under a unified hierarchy with symmetric `addFirst`/`addLast`, `getFirst`/`getLast`, and `reversed()` view methods.
