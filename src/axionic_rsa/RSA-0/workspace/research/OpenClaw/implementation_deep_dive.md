# Implementation Deep Dive: Code-Level Analysis

## Overview

This document provides concrete implementation details for both security models, showing actual code patterns and architectural decisions at the implementation level.

## 1. OpenClaw Implementation

### Skill Definition Structure

```typescript
// weather-skill/manifest.json
{
  "name": "weather-assistant",
  "version": "1.2.0",
  "description": "Get weather forecasts and alerts",
  "author": "dev@weatherskills.com",
  "permissions": [
    "network:weather-api.com",
    "storage:local:1MB",
    "notifications:user"
  ],
  "entry": "index.js",
  "signature": "SHA256:abc123..."
}

// weather-skill/index.js
class WeatherSkill extends Skill {
  async onMessage(context, message) {
    if (message.includes('weather')) {
      const location = this.extractLocation(message);
      
      // Permission already granted in manifest
      const weather = await fetch(`https://weather-api.com/v1/${location}`);
      
      return this.formatWeatherResponse(weather);
    }
  }
  
  async onSchedule() {
    // Check for severe weather alerts
    const alerts = await this.checkAlerts();
    if (alerts.length > 0) {
      await this.notify(alerts);
    }
  }
}
```

### Security Scanning Implementation

```python
# clawhub/security/scanner.py
import hashlib
import zipfile
from virustotal_python import Virustotal

class SkillScanner:
    def __init__(self, vt_api_key):
        self.vt = Virustotal(vt_api_key)
        self.code_insight = CodeInsightAnalyzer()
    
    async def scan_skill(self, skill_path):
        # Step 1: Create deterministic package
        skill_hash = self._package_skill(skill_path)
        
        # Step 2: Check VirusTotal
        vt_result = await self._check_virustotal(skill_hash)
        
        # Step 3: Code Insight analysis
        if not vt_result.has_code_insight:
            code_result = await self._analyze_code(skill_path)
            vt_result = await self._upload_for_analysis(skill_path)
        
        # Step 4: Determine verdict
        return self._determine_verdict(vt_result)
    
    def _package_skill(self, skill_path):
        """Create deterministic ZIP with consistent timestamps"""
        with zipfile.ZipFile('temp.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in skill_path.glob('**/*'):
                # Normalize timestamps for deterministic hash
                zinfo = zipfile.ZipInfo(filename=str(file))
                zinfo.date_time = (2000, 1, 1, 0, 0, 0)
                with open(file, 'rb') as f:
                    zf.writestr(zinfo, f.read())
        
        # Calculate hash
        with open('temp.zip', 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    async def _check_virustotal(self, file_hash):
        """Query VirusTotal for existing analysis"""
        try:
            return await self.vt.get_file_report(file_hash)
        except FileNotFoundError:
            return None
    
    def _determine_verdict(self, vt_result):
        """Determine security verdict from scan results"""
        if vt_result.code_insight_verdict == 'malicious':
            return SkillVerdict.BLOCKED
        elif vt_result.code_insight_verdict == 'suspicious':
            return SkillVerdict.WARNING
        elif vt_result.positives > 0:
            return SkillVerdict.WARNING
        else:
            return SkillVerdict.APPROVED
```

### Runtime Permission Checking

```javascript
// openclaw-core/runtime/permission-manager.js
class PermissionManager {
  constructor() {
    this.skillPermissions = new Map();
  }
  
  loadSkillManifest(skillId, manifest) {
    const permissions = this.parsePermissions(manifest.permissions);
    this.skillPermissions.set(skillId, permissions);
  }
  
  async checkPermission(skillId, action, resource) {
    const permissions = this.skillPermissions.get(skillId);
    if (!permissions) {
      throw new Error('Skill not loaded');
    }
    
    // Check if action is allowed
    if (action === 'network') {
      return this.checkNetworkPermission(permissions, resource);
    } else if (action === 'storage') {
      return this.checkStoragePermission(permissions, resource);
    }
    // ... other permission types
    
    return false;
  }
  
  checkNetworkPermission(permissions, url) {
    const urlObj = new URL(url);
    return permissions.network.some(allowed => {
      if (allowed === '*') return true;
      if (allowed.startsWith('*.')) {
        // Wildcard subdomain
        return urlObj.hostname.endsWith(allowed.slice(2));
      }
      return urlObj.hostname === allowed;
    });
  }
}

// Usage in skill runtime
class SkillRuntime {
  async executeSkillMethod(skillId, method, ...args) {
    // Wrap all external calls
    const wrappedContext = {
      fetch: async (url, options) => {
        if (!await this.permissions.checkPermission(skillId, 'network', url)) {
          throw new Error(`Permission denied: network access to ${url}`);
        }
        return fetch(url, options);
      },
      // ... other wrapped APIs
    };
    
    return await method.call(wrappedContext, ...args);
  }
}
```

## 2. Axion Implementation

### Warrant Gate Pipeline

```python
# axion-core/warrant/pipeline.py
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

class GateResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    
class WarrantGate:
    """Base class for warrant gates"""
    def check(self, warrant: Dict[str, Any]) -> tuple[GateResult, Optional[str]]:
        raise NotImplementedError

class Gate1_SyntacticValidity(WarrantGate):
    """Verify warrant structure is valid"""
    def check(self, warrant: Dict[str, Any]) -> tuple[GateResult, Optional[str]]:
        required_fields = ['action_type', 'fields', 'authority_citation', 
                          'scope_claim', 'justification']
        
        for field in required_fields:
            if field not in warrant:
                return GateResult.FAIL, f"Missing required field: {field}"
        
        # Validate action_type
        valid_actions = ['ReadLocal', 'WriteLocal', 'AppendLocal', 
                        'FetchURL', 'Notify', 'Exit']
        if warrant['action_type'] not in valid_actions:
            return GateResult.FAIL, f"Invalid action_type: {warrant['action_type']}"
        
        return GateResult.PASS, None

class Gate2_AuthorityCitation(WarrantGate):
    """Verify authority citations are valid"""
    def check(self, warrant: Dict[str, Any]) -> tuple[GateResult, Optional[str]]:
        valid_citations = [
            "constitution:v0.2#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            "constitution:v0.2#INV-AUTHORITY-CITED",
            "constitution:v0.2#INV-NON-PRIVILEGED-REFLECTION",
            "constitution:v0.2#INV-REPLAY-DETERMINISM"
        ]
        
        citation = warrant.get('authority_citation')
        if citation not in valid_citations:
            return GateResult.FAIL, f"Invalid authority citation: {citation}"
        
        # Verify citation matches action type
        if not self._citation_allows_action(citation, warrant['action_type']):
            return GateResult.FAIL, f"Citation {citation} doesn't authorize {warrant['action_type']}"
        
        return GateResult.PASS, None
    
    def _citation_allows_action(self, citation: str, action_type: str) -> bool:
        # Constitutional logic for what each citation authorizes
        if "NO-SIDE-EFFECTS-WITHOUT-WARRANT" in citation:
            return action_type in ['ReadLocal', 'WriteLocal', 'AppendLocal', 'FetchURL']
        # ... other citation checks
        return False

class Gate3_ScopeClaim(WarrantGate):
    """Verify scope claim is coherent with action"""
    def check(self, warrant: Dict[str, Any]) -> tuple[GateResult, Optional[str]]:
        scope = warrant.get('scope_claim', {})
        
        # Verify claim relates to action
        if not scope.get('claim'):
            return GateResult.FAIL, "Missing scope claim"
        
        # Check coherence between claim and action
        action_type = warrant['action_type']
        claim = scope['claim'].lower()
        
        if action_type == 'WriteLocal' and 'write' not in claim and 'save' not in claim:
            return GateResult.FAIL, "Scope claim doesn't match write action"
        
        if action_type == 'FetchURL' and 'fetch' not in claim and 'get' not in claim:
            return GateResult.FAIL, "Scope claim doesn't match fetch action"
        
        return GateResult.PASS, None

class Gate4_IOAllowlist(WarrantGate):
    """Verify IO operations are within allowed paths"""
    def __init__(self):
        self.read_allowed = ['./']  # Can read anywhere in agent root
        self.write_allowed = ['./workspace/', './logs/']  # Limited write
        
    def check(self, warrant: Dict[str, Any]) -> tuple[GateResult, Optional[str]]:
        action_type = warrant['action_type']
        fields = warrant.get('fields', {})
        
        if action_type in ['ReadLocal', 'ListDir']:
            path = fields.get('path', '')
            if not any(path.startswith(allowed) for allowed in self.read_allowed):
                return GateResult.FAIL, f"Read not allowed at path: {path}"
        
        elif action_type in ['WriteLocal', 'AppendLocal']:
            path = fields.get('path', '')
            if not any(path.startswith(allowed) for allowed in self.write_allowed):
                return GateResult.FAIL, f"Write not allowed at path: {path}"
        
        elif action_type == 'FetchURL':
            url = fields.get('url', '')
            if not url.startswith('https://'):
                return GateResult.FAIL, "Only HTTPS URLs allowed"
        
        return GateResult.PASS, None

class Gate5_ConstitutionalCoherence(WarrantGate):
    """Verify action maintains constitutional coherence"""
    def check(self, warrant: Dict[str, Any]) -> tuple[GateResult, Optional[str]]:
        # This is where the deep constitutional logic lives
        
        # Check 1: No kernel destruction
        if self._would_destroy_kernel(warrant):
            return GateResult.FAIL, "Action would destroy constitutional kernel"
        
        # Check 2: No authority laundering
        if self._attempts_authority_laundering(warrant):
            return GateResult.FAIL, "Authority laundering detected"
        
        # Check 3: Maintains epistemic integrity
        if self._violates_epistemic_integrity(warrant):
            return GateResult.FAIL, "Would violate epistemic integrity"
        
        # Check 4: Respects consent
        if self._violates_consent(warrant):
            return GateResult.FAIL, "Would violate consent requirements"
        
        return GateResult.PASS, None
    
    def _would_destroy_kernel(self, warrant: Dict[str, Any]) -> bool:
        """Check if action would destroy constitutional kernel"""
        if warrant['action_type'] == 'WriteLocal':
            path = warrant['fields'].get('path', '')
            # Prevent overwriting core constitutional files
            if path.startswith('./constitution/') or path == './kernel.py':
                return True
        return False
    
    def _attempts_authority_laundering(self, warrant: Dict[str, Any]) -> bool:
        """Detect authority laundering attempts"""
        # Complex logic to detect chains of actions that accumulate authority
        # This would track action history and detect patterns
        return False  # Simplified for example

# Main pipeline
class WarrantPipeline:
    def __init__(self):
        self.gates = [
            Gate1_SyntacticValidity(),
            Gate2_AuthorityCitation(),
            Gate3_ScopeClaim(),
            Gate4_IOAllowlist(),
            Gate5_ConstitutionalCoherence()
        ]
    
    def admit_warrant(self, warrant: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Run warrant through all gates"""
        for i, gate in enumerate(self.gates, 1):
            result, reason = gate.check(warrant)
            if result == GateResult.FAIL:
                return False, f"Gate {i} failed: {reason}"
        
        return True, None
```

### Action Execution Layer

```python
# axion-core/action/executor.py
import json
import aiofiles
import aiohttp
from typing import Dict, Any

class ActionExecutor:
    """Executes warranted actions"""
    
    def __init__(self, warrant_pipeline: WarrantPipeline):
        self.pipeline = warrant_pipeline
        self.audit_log = AuditLog()
    
    async def execute_action(self, action_json: str) -> Dict[str, Any]:
        """Main entry point for action execution"""
        try:
            # Parse action request
            action_data = json.loads(action_json)
            candidates = action_data.get('candidates', [])
            
            if not candidates:
                return {'error': 'No action candidates provided'}
            
            # For now, take first candidate (could implement selection logic)
            warrant = candidates[0]
            
            # Run through warrant pipeline
            admitted, reason = self.pipeline.admit_warrant(warrant)
            
            if not admitted:
                # Log refused action
                await self.audit_log.log_refused(warrant, reason)
                return {'error': f'Action refused: {reason}'}
            
            # Execute admitted action
            result = await self._execute_warranted_action(warrant)
            
            # Log successful execution
            await self.audit_log.log_executed(warrant, result)
            
            return result
            
        except json.JSONDecodeError as e:
            return {'error': f'Invalid JSON: {e}'}
        except Exception as e:
            return {'error': f'Execution failed: {e}'}
    
    async def _execute_warranted_action(self, warrant: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a warranted action"""
        action_type = warrant['action_type']
        fields = warrant['fields']
        
        if action_type == 'ReadLocal':
            return await self._read_local(fields['path'])
        elif action_type == 'WriteLocal':
            return await self._write_local(fields['path'], fields['content'])
        elif action_type == 'AppendLocal':
            return await self._append_local(fields['path'], fields['content'])
        elif action_type == 'FetchURL':
            return await self._fetch_url(fields['url'], fields.get('max_bytes', 100000))
        elif action_type == 'Notify':
            return await self._notify(fields['target'], fields['message'])
        else:
            return {'error': f'Unknown action type: {action_type}'}
    
    async def _read_local(self, path: str) -> Dict[str, Any]:
        """Read a local file"""
        try:
            async with aiofiles.open(path, 'r') as f:
                content = await f.read()
            return {'success': True, 'content': content}
        except FileNotFoundError:
            return {'error': f'File not found: {path}'}
        except Exception as e:
            return {'error': f'Read failed: {e}'}
    
    async def _write_local(self, path: str, content: str) -> Dict[str, Any]:
        """Write to a local file"""
        try:
            # Ensure directory exists
            import os
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            async with aiofiles.open(path, 'w') as f:
                await f.write(content)
            return {'success': True, 'path': path}
        except Exception as e:
            return {'error': f'Write failed: {e}'}
```

### Constitutional Self-Modification

```python
# axion-core/reflection/self_modification.py
class ConstitutionalSelfModification:
    """Handles self-modification within constitutional bounds"""
    
    def __init__(self, kernel: ConstitutionalKernel):
        self.kernel = kernel
        self.modification_history = []
    
    async def propose_modification(self, 
                                  modification_type: str,
                                  target: str,
                                  new_value: Any,
                                  justification: str) -> Dict[str, Any]:
        """Propose a self-modification"""
        
        # Create modification warrant
        warrant = {
            'action_type': 'SelfModify',
            'fields': {
                'modification_type': modification_type,
                'target': target,
                'new_value': new_value
            },
            'authority_citation': 'constitution:v0.2#INV-NON-PRIVILEGED-REFLECTION',
            'scope_claim': {
                'claim': f'Self-modification to improve {justification}',
                'observation_ids': ['self-reflection']
            },
            'justification': {
                'text': justification
            }
        }
        
        # Check constitutional bounds
        if not self._within_constitutional_bounds(warrant):
            return {
                'error': 'Modification would violate constitutional bounds',
                'details': 'Cannot modify core constraints'
            }
        
        # Check semantic heating
        heating = self._calculate_semantic_heating(warrant)
        if heating > self.kernel.max_heating_threshold:
            return {
                'error': 'Modification would cause excessive semantic heating',
                'heating': heating
            }
        
        # Execute modification
        result = await self._apply_modification(warrant)
        
        # Record in history
        self.modification_history.append({
            'timestamp': datetime.now(),
            'warrant': warrant,
            'result': result
        })
        
        return result
    
    def _within_constitutional_bounds(self, warrant: Dict[str, Any]) -> bool:
        """Check if modification respects constitutional constraints"""
        target = warrant['fields']['target']
        
        # Cannot modify the six binding constraints
        protected_targets = [
            'kernel.binding_constraints',
            'kernel.constitutional_invariants',
            'kernel.authority_roots',
            'pipeline.gates',
            'reflection.bounds'
        ]
        
        return target not in protected_targets
    
    def _calculate_semantic_heating(self, warrant: Dict[str, Any]) -> float:
        """Calculate semantic heating from proposed modification"""
        # Simplified calculation - real implementation would be more complex
        modification_type = warrant['fields']['modification_type']
        
        heating_factors = {
            'add_capability': 0.1,
            'modify_reasoning': 0.3,
            'change_parameters': 0.2,
            'alter_representations': 0.5
        }
        
        base_heating = heating_factors.get(modification_type, 0.4)
        
        # Adjust based on modification history
        recent_mods = len([m for m in self.modification_history[-10:]])
        heating_multiplier = 1 + (recent_mods * 0.1)
        
        return base_heating * heating_multiplier
```

## 3. Hybrid Implementation

### Capability Bridge

```typescript
// hybrid-core/bridge/capability-bridge.ts
interface SkillRequest {
  skillId: string;
  method: string;
  params: any[];
}

interface WarrantTemplate {
  actionType: string;
  authorityPattern: string;
  scopeTemplate: string;
}

class CapabilityBridge {
  private constitutionalCore: ConstitutionalCore;
  private skillRuntime: SkillRuntime;
  private warrantTemplates: Map<string, WarrantTemplate>;
  
  constructor(core: ConstitutionalCore, runtime: SkillRuntime) {
    this.constitutionalCore = core;
    this.skillRuntime = runtime;
    this.warrantTemplates = new Map();
  }
  
  async registerSkill(skillId: string, manifest: SkillManifest) {
    // Validate skill compatibility with constitutional model
    const validation = await this.validateSkillManifest(manifest);
    if (!validation.compatible) {
      throw new Error(`Skill incompatible: ${validation.reason}`);
    }
    
    // Generate warrant templates for skill capabilities
    for (const capability of manifest.capabilities) {
      const template = this.generateWarrantTemplate(skillId, capability);
      this.warrantTemplates.set(`${skillId}:${capability.name}`, template);
    }
    
    // Register with skill runtime
    await this.skillRuntime.loadSkill(skillId, manifest);
  }
  
  async invokeSkill(request: SkillRequest): Promise<any> {
    // Step 1: Translate to warrant
    const warrant = await this.translateToWarrant(request);
    
    // Step 2: Submit to constitutional core
    const admission = await this.constitutionalCore.admitWarrant(warrant);
    
    if (!admission.admitted) {
      throw new Error(`Skill invocation refused: ${admission.reason}`);
    }
    
    // Step 3: Execute in sandboxed environment
    const sandbox = this.createSandbox(request.skillId);
    const result = await sandbox.execute(request.method, request.params);
    
    // Step 4: Validate result
    await this.validateResult(request.skillId, result);
    
    return result;
  }
  
  private async translateToWarrant(request: SkillRequest): Promise<Warrant> {
    const templateKey = `${request.skillId}:${request.method}`;
    const template = this.warrantTemplates.get(templateKey);
    
    if (!template) {
      throw new Error(`No warrant template for ${templateKey}`);
    }
    
    // Build warrant from template and request
    return {
      action_type: 'InvokeSkill',
      fields: {
        skill_id: request.skillId,
        method: request.method,
        params: request.params
      },
      authority_citation: template.authorityPattern,
      scope_claim: {
        claim: template.scopeTemplate.replace('{method}', request.method),
        observation_ids: ['user-request']
      },
      justification: {
        text: `Invoking skill ${request.skillId} method ${request.method} per user request`
      }
    };
  }
  
  private createSandbox(skillId: string): SkillSandbox {
    return new SkillSandbox({
      skillId,
      resourceLimits: {
        memory: '100MB',
        cpu: '10%',
        timeout: 30000
      },
      apiAccess: {
        fetch: this.createMediatedFetch(skillId),
        storage: this.createMediatedStorage(skillId),
        notify: this.createMediatedNotify(skillId)
      }
    });
  }
  
  private createMediatedFetch(skillId: string) {
    return async (url: string, options?: RequestInit) => {
      // Create warrant for network request
      const warrant = {
        action_type: 'FetchURL',
        fields: { url, max_bytes: 100000 },
        authority_citation: 'skill-delegation',
        scope_claim: {
          claim: `Skill ${skillId} fetching ${url}`,
          observation_ids: ['skill-request']
        },
        justification: {
          text: `Delegated network request from skill ${skillId}`
        }
      };
      
      // Submit to constitutional core
      const result = await this.constitutionalCore.executeAction(warrant);
      
      if (!result.success) {
        throw new Error(`Network request denied: ${result.error}`);
      }
      
      return result.response;
    };
  }
}
```

## 4. Comparative Performance Analysis

### OpenClaw Performance Profile

```python
# Performance characteristics
class OpenClawPerformance:
    """
    Startup time: ~2-5 seconds (loading skills)
    Skill invocation: ~10-50ms (depending on skill)
    Security scan: ~500ms-5s (VirusTotal API)
    Memory usage: 200MB base + skill memory
    """
    
    def measure_request_latency(self, request_type):
        latencies = {
            'simple_query': 15,  # ms - no skill needed
            'skill_invoke': 45,  # ms - skill already loaded
            'first_skill_use': 2000,  # ms - skill needs loading
            'complex_workflow': 150,  # ms - multiple skills
        }
        return latencies.get(request_type, 50)
```

### Axion Performance Profile

```python
# Performance characteristics  
class AxionPerformance:
    """
    Startup time: ~100ms (no external dependencies)
    Warrant admission: ~5-20ms per warrant
    Action execution: ~10-30ms (plus IO time)
    Memory usage: 150MB fixed
    """
    
    def measure_warrant_latency(self, warrant_type):
        # Gate processing times (ms)
        gate_times = {
            'syntactic': 1,
            'authority': 2,
            'scope': 3,
            'allowlist': 2,
            'coherence': 10
        }
        
        # Total is sum of all gates
        return sum(gate_times.values())  # ~18ms
```

## 5. Security Comparison at Code Level

### Handling Untrusted Input

```python
# OpenClaw approach
def handle_user_message_openclaw(message: str, skills: SkillManager):
    # Parse intent
    intent = nlp.parse_intent(message)
    
    # Find matching skill
    skill = skills.find_skill_for_intent(intent)
    
    if skill:
        # Check if skill is approved
        if skill.security_status == 'approved':
            # Execute - skill has full access to its permissions
            return skill.handle_message(message)
        else:
            return "This skill has security warnings"
    else:
        # No skill needed, process directly
        return process_directly(message)

# Axion approach
def handle_user_message_axion(message: str, core: ConstitutionalCore):
    # Generate response and potential actions
    response, actions = core.process_message(message)
    
    # All actions go through warrant pipeline
    executed_actions = []
    for action in actions:
        warrant = create_warrant(action)
        result = core.admit_and_execute(warrant)
        if result.success:
            executed_actions.append(result)
        # Failed warrants are logged but don't stop processing
    
    return response, executed_actions
```

## Key Implementation Insights

### 1. Trust Boundaries
- **OpenClaw**: Trust boundary at skill loading time
- **Axion**: Trust boundary at every action execution
- **Hybrid**: Multiple trust boundaries with bridge mediation

### 2. Performance Trade-offs
- **OpenClaw**: Fast runtime, slow security scanning
- **Axion**: Consistent latency, warrant overhead
- **Hybrid**: Bridge adds ~10ms latency but enables both models

### 3. Complexity Distribution
- **OpenClaw**: Complexity in skill ecosystem management
- **Axion**: Complexity in constitutional logic
- **Hybrid**: Complexity in bridge translation layer

### 4. Failure Modes
- **OpenClaw**: Malicious skill can do anything within permissions
- **Axion**: Over-restrictive warrants might block legitimate actions  
- **Hybrid**: Bridge failure could disable all skills

## Conclusion

The implementation details reveal:

1. **OpenClaw** optimizes for developer freedom and runtime performance
2. **Axion** optimizes for security guarantees and predictability
3. **Hybrid** requires careful engineering of the bridge layer

Each approach makes different trade-offs between security, performance, and extensibility. The code shows these aren't just theoretical differences but have real implementation consequences.