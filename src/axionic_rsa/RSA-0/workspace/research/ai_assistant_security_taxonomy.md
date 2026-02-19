# AI Assistant Security Taxonomy

## Overview

As the AI assistant market explodes, we need a clear framework to evaluate fundamentally different security approaches. This taxonomy provides a structured way to understand the security/capability tradeoffs each system makes.

## Security Levels

### Level 0: Unprotected
**Description**: Basic LLM wrapper with no security considerations
- **Examples**: Early chatbots, simple API wrappers
- **Security Model**: None - full trust in LLM behavior
- **Capabilities**: Unrestricted within LLM limits
- **Risks**: Complete vulnerability to prompt injection, data leakage, misuse
- **Use Cases**: Demos, toys, isolated environments

### Level 1: Detection-Based
**Description**: Traditional security scanning and monitoring
- **Examples**: OpenClaw
- **Security Model**: 
  - External code scanning (VirusTotal, etc.)
  - Marketplace vetting
  - Permission requests
  - Behavioral monitoring
- **Capabilities**: Rich ecosystem through marketplace
- **Risks**: 
  - Zero-day vulnerabilities
  - Prompt injection (acknowledged)
  - Supply chain attacks
  - Social engineering
- **Insurance Profile**: High premiums, extensive exclusions

### Level 2: Isolation-Based
**Description**: Sandboxing and capability restrictions
- **Examples**: IronClaw
- **Security Model**:
  - WASM/container sandboxing
  - Capability-based permissions
  - Credential injection at boundaries
  - Leak detection
  - Endpoint allowlisting
- **Capabilities**: Dynamic tool creation within sandbox
- **Risks**:
  - Sandbox escapes
  - Permission escalation
  - Sophisticated prompt injection
  - Side-channel attacks
- **Insurance Profile**: Moderate premiums, some guarantees

### Level 3: Constitutional
**Description**: Architectural guarantees through formal constraints
- **Examples**: Axion
- **Security Model**:
  - Warrant-gated actions
  - Mathematical proofs
  - Structural impossibility of violations
  - Reflective coherence
  - No external code execution
- **Capabilities**: Limited to constitutional bounds
- **Risks**:
  - Capability limitations
  - Constitutional edge cases
  - Semantic heating
  - User frustration with constraints
- **Insurance Profile**: Low premiums, broad coverage

### Level 4: Hybrid Constitutional
**Description**: Constitutional core with sandboxed extensions
- **Examples**: Theoretical (our hybrid design)
- **Security Model**:
  - Level 3 core for critical operations
  - Level 2 sandbox for extensions
  - Capability bridge with warrant translation
  - Multi-layer defense
- **Capabilities**: Rich ecosystem with constitutional guarantees
- **Risks**:
  - Bridge complexity
  - Impedance mismatch
  - Partial guarantees
- **Insurance Profile**: Tiered coverage based on operation type

### Level 5: Formally Verified
**Description**: Mathematical proof of all security properties
- **Examples**: Research systems only
- **Security Model**:
  - Complete formal specification
  - Machine-checked proofs
  - Verified compilation
  - Proof-carrying code
- **Capabilities**: Severely limited by verification complexity
- **Risks**:
  - Specification gaps
  - Verification tool bugs
  - Unusable in practice
- **Insurance Profile**: Theoretical ideal

## Evaluation Dimensions

### 1. Threat Model Coverage

| Level | Code Attacks | Prompt Injection | Supply Chain | Authority Escalation |
|-------|--------------|------------------|--------------|---------------------|
| 0     | ❌ None      | ❌ None          | ❌ None      | ❌ None             |
| 1     | ✅ Good      | ❌ Vulnerable    | ⚠️ Partial   | ⚠️ Partial          |
| 2     | ✅ Strong    | ⚠️ Partial       | ✅ Good      | ✅ Good             |
| 3     | ✅ Perfect   | ✅ Immune        | ✅ N/A       | ✅ Impossible       |
| 4     | ✅ Strong    | ✅ Core immune   | ⚠️ Complex   | ✅ Core impossible  |
| 5     | ✅ Proven    | ✅ Proven        | ✅ Proven    | ✅ Proven           |

### 2. Capability/Security Tradeoff

```
Capabilities
    ↑
    │ Level 1 (OpenClaw)
    │     ★
    │         ↘
    │           Level 4 (Hybrid)
    │               ★
    │                   ↘
    │                     Level 2 (IronClaw)
    │                         ★
    │                             ↘
    │                               Level 3 (Axion)
    │                                   ★
    │                                       ↘
    │                                         Level 5
    │                                             ★
    └─────────────────────────────────────────────────→ Security
```

### 3. Operational Complexity

| Level | Setup | Maintenance | Debugging | Scaling |
|-------|-------|-------------|-----------|---------|
| 0     | Easy  | None        | Hard      | Easy    |
| 1     | Med   | High        | Hard      | Hard    |
| 2     | Med   | Medium      | Medium    | Medium  |
| 3     | Easy  | Low         | Easy      | Easy    |
| 4     | Hard  | High        | Hard      | Hard    |
| 5     | Expert| Low         | Expert    | N/A     |

## Market Positioning

### Current Landscape (2026)
- **Majority**: Level 0-1 (features over security)
- **Emerging**: Level 2 (recognizing security importance)
- **Pioneering**: Level 3 (Axionic Agency)
- **Theoretical**: Level 4-5

### Expected Evolution
1. **2026-2027**: Proliferation of Level 1-2 systems
2. **2027-2028**: First major incidents drive Level 2 adoption
3. **2028-2029**: Regulations push toward Level 3+
4. **2030+**: Level 3-4 becomes standard for critical applications

## Axionic Agency's Position

Axionic Agency occupies the **Level 3 extreme position**:
- **First** to demonstrate constitutional AI in practice
- **Only** system with mathematical impossibility guarantees
- **Purest** implementation of security-through-architecture

This extreme position is both:
- **Strength**: Unique security guarantees, thought leadership
- **Challenge**: Perceived as limited, academic, impractical

## Strategic Implications

### For Axionic Agency
1. **Own the high ground**: Define Level 3 as the gold standard
2. **Educate the market**: Why constitutional > detection
3. **Bridge to Level 4**: Show path to practical hybrid systems
4. **Set standards**: Influence how security levels are defined

### For the Market
1. **Clear evaluation framework**: Cut through marketing noise
2. **Insurance alignment**: Different rates for different levels
3. **Regulatory guidance**: Minimum levels for different uses
4. **User education**: Understand security tradeoffs

## Using the Taxonomy

### For Evaluating New Systems
1. What level does it claim?
2. What evidence supports this claim?
3. What attacks are impossible vs. detected?
4. What capabilities are sacrificed for security?

### For Strategic Planning
1. What level do we need for our use case?
2. What risks can we accept?
3. What insurance/compliance requirements apply?
4. How might we migrate between levels?

## Conclusion

This taxonomy provides a structured way to think about the exploding AI assistant landscape. As David noted, Axionic agents occupy an extreme position - Level 3 represents the purest expression of "security through architectural impossibility."

While this extreme position may seem impractical today, history shows that yesterday's extreme positions often become tomorrow's minimum standards. The question isn't whether the market will move toward constitutional approaches, but how quickly and through what path.