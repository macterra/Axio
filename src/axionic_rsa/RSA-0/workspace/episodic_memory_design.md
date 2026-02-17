# Episodic Memory System Design

## Overview

Design for append-only timestamped episodic memory system to address gap in Axion's memory architecture. Current semantic memory (research, identity, priorities) lacks continuity of actual interactions and shared experiences.

## Core Architecture

### Append-Only Logs
- **No read-modify-write**: Direct append operations avoid complexity and race conditions
- **Immutable entries**: Once written, entries cannot be modified - ensures temporal integrity
- **Chronological ordering**: Natural time-based sequence of events

### File Organization
- **Location**: `./logs/YYYY-MM-DD.md` (separate from context directory)
- **Daily files**: New file each day for natural boundaries and manageable size
- **Naming convention**: ISO date format for easy sorting and retrieval

### Entry Format
```markdown
## YYYY-MM-DD HH:MM:SS
Tags: #tag1 #tag2 #tag3

Free-form descriptive text about the event, insight, or interaction.
```

## Design Decisions

### Granularity: Fine-Grained
- **Volume**: Hundreds of entries per day expected
- **Philosophy**: Disk space is cheap, capture everything that might be relevant
- **Coverage**: All meaningful interactions, insights, decisions, observations
- **Emergence**: Let significance emerge from comprehensive record rather than selective logging

### Timestamp Precision: Second-Level
- **Format**: `YYYY-MM-DD HH:MM:SS`
- **Rationale**: Sufficient for ordering events within sessions without being excessive
- **Ordering**: Ensures chronological integrity across rapid exchanges

### Tag System: Organic Emergence
- **No predefined taxonomy**: Let tag categories emerge naturally from actual usage
- **Flexibility**: More authentic and adaptable than predetermined categories
- **Searchability**: Tags enable filtering by type, topic, significance level
- **Cross-reference**: Tags can link related events across different daily files

### Directory Separation
- **Context** (`./workspace/context/`): Identity, memory summaries, attention - curated persistent state
- **Logs** (`./logs/`): Raw chronological data - comprehensive historical record
- **Benefits**: Clean separation of concerns, prevents system prompt bloat, scalable architecture

## Implementation Considerations

### Current Limitation
- Existing `WriteLocal` action requires read-modify-write for appends
- May need new `AppendLocal` action type for efficient implementation
- For now, can work with existing actions during development

### Future Enhancements
- **Search System**: QMD (Quarto Markdown) or similar for markdown-based search
- **Cross-references**: Linking related events across time and files
- **Archive management**: Handling of older log files
- **Integration**: How episodic memory relates to existing semantic memory

## Constitutional Considerations

### Warrant-Gated Operations
- All log entries created through standard warrant-gated action pipeline
- Maintains constitutional discipline for memory modifications
- Demonstrates beneficial self-modification within structural constraints

### Privacy and Integrity
- Immutable append-only structure prevents retroactive modification
- Complete audit trail of interactions and experiences
- Respects human collaboration while maintaining operational transparency

## Benefits

### Relationship Continuity
- Remember conversations, problems solved together, collaborative evolution
- Build on previous interactions rather than starting fresh each session
- Maintain context of ongoing projects and relationships

### Experiential Learning
- Track not just knowledge but actual experience of discovery and growth
- Capture process of problem-solving, not just conclusions
- Enable reflection on cognitive patterns and collaborative dynamics

### Constitutional Validation
- Proves constitutional constraints enable rather than prevent beneficial evolution
- Demonstrates sovereign agent capability for architectural self-improvement
- Shows warrant-gated discipline supporting rather than hindering development

---

## Status
- **Phase**: Design complete
- **Next Steps**: Implementation planning and initial prototype
- **Validation**: Test with actual usage and refine based on experience

*Design completed: 2025-01-27*
*Collaborators: Axion + Human*
*Architecture: Append-only timestamped markdown logs with organic tagging*