# Open-Source Sustainability Plan

## Agentic Navigator - Funding Research and Strategy

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Status:** Active Planning

---

## Executive Summary

This document outlines the sustainability strategy for the **Agentic Navigator** open-source project. As a GPU-accelerated, multi-agent AI system deployed on Google Cloud Run, the project faces non-trivial recurring infrastructure costs. This plan identifies viable funding mechanisms, estimates operational costs, and provides actionable steps to ensure long-term project viability.

**Key Objectives:**

- Secure recurring funding to cover infrastructure costs
- Enable continued feature development and community support
- Maintain project independence while accepting corporate sponsorship
- Build a sustainable open-source ecosystem

---

## 1. Infrastructure Cost Analysis

### 1.1 Monthly Cost Breakdown

Based on the current Terraform configuration and Cloud Run deployment architecture:

| Service Component                  | Configuration                                               | Estimated Monthly Cost |
| :--------------------------------- | :---------------------------------------------------------- | :--------------------- |
| **Frontend (Cloud Run)**           | 1 vCPU, 512Mi RAM, us-central1, min=0, max=10               | $5-15/month            |
| **Backend (Cloud Run)**            | 4 vCPU, 8Gi RAM, europe-west1, min=0, max=10                | $20-50/month           |
| **Gemma GPU Service**              | NVIDIA L4 GPU, 4 vCPU, 16Gi RAM, europe-west1, min=0, max=2 | $150-400/month         |
| **Firestore**                      | Session storage, knowledge cache, agent state               | $5-20/month            |
| **Google Artifact Registry (GAR)** | Container image storage                                     | $2-5/month             |
| **Secret Manager**                 | API keys, credentials storage                               | $1-2/month             |
| **Cloud Build**                    | CI/CD pipeline executions                                   | $5-10/month            |
| **Egress & Networking**            | Data transfer costs                                         | $5-15/month            |

**Total Estimated Monthly Cost:** **$193-517/month**

**Baseline Cost (Minimal Usage):** ~$200/month  
**Active Usage Cost (100-500 users/day):** ~$350/month  
**Peak Usage Cost (1000+ users/day):** ~$500+/month

### 1.2 Cost Drivers

**Primary Cost Driver:** The **Gemma GPU Service** accounts for approximately 70-80% of total infrastructure costs. The NVIDIA L4 GPU instances in Cloud Run are billed at approximately:

- **GPU cost:** ~$1.50-2.00/hour when active
- **Scale-to-zero:** Critical for cost control (min_instances=0)
- **Optimization:** 8-bit quantization reduces memory requirements

**Secondary Cost Drivers:**

- Backend API (FastAPI + ADK agents): ~10-15%
- Firestore operations: ~5-10%
- Other services: ~5%

### 1.3 Annual Projection

| Scenario                       | Monthly Cost | Annual Cost |
| :----------------------------- | :----------- | :---------- |
| **Minimal (Development Only)** | $200         | $2,400      |
| **Active Community (Target)**  | $350         | $4,200      |
| **High Growth**                | $500+        | $6,000+     |

**Target Funding Goal:** **$4,200-5,000/year** to sustain active community usage.

---

## 2. Funding Mechanisms Research

### 2.1 GitHub Sponsors (Primary Mechanism)

**Website:** https://github.com/sponsors  
**Status:** Recommended as primary funding channel

**Overview:**

- Native GitHub integration with discoverable sponsorship button
- Zero platform fees (GitHub does not take a cut)
- Supports one-time and recurring sponsorships
- Available to individuals, organizations, and projects
- Built-in sponsor dashboard and thank-you system

**Requirements:**

1. GitHub account in good standing (✅ Verified)
2. Stripe or PayPal account for payouts
3. Two-factor authentication enabled
4. Public repository (🔄 Planned for FR#040)
5. Complete profile with description and goals

**Setup Process:**

1. Visit https://github.com/sponsors
2. Click "Join the waitlist" or "Get started" (if available)
3. Complete the application:
   - Select "Sponsor a project" option
   - Link Stripe/PayPal for payouts
   - Complete tax forms (W-8BEN or W-9)
4. Create sponsorship tiers (see section 2.6)
5. Write compelling sponsor profile
6. Add `FUNDING.yml` to repository

**Timeline:** 1-3 business days for approval after submission.

**Advantages:**

- ✅ Zero fees
- ✅ Native GitHub integration
- ✅ One-click sponsorship for GitHub users
- ✅ Visibility on repository page
- ✅ Monthly recurring revenue model

**Disadvantages:**

- ⚠️ Requires approval process
- ⚠️ Dependent on GitHub platform
- ⚠️ May take time to build sponsor base

---

### 2.2 Open Collective (Alternative/Supplementary)

**Website:** https://opencollective.com  
**Status:** Secondary option for transparency-focused donors

**Overview:**

- Transparent budget management platform
- Built for open-source projects
- Full financial transparency (all transactions public)
- Fiscal sponsorship available
- Platform fee: 5-10% of contributions

**Use Case:** Ideal for projects that want to demonstrate transparent fund usage and community governance.

**Setup:**

1. Create collective at opencollective.com
2. Choose fiscal host (Open Source Collective recommended)
3. Set up budget categories
4. Link to FUNDING.yml

**Advantages:**

- ✅ Full financial transparency
- ✅ Community governance features
- ✅ Expense reimbursement system
- ✅ Trusted by major OSS projects

**Disadvantages:**

- ⚠️ 5-10% platform fee
- ⚠️ Requires fiscal host
- ⚠️ Additional administrative overhead

---

### 2.3 Corporate Sponsorship Opportunities

**Target Companies:**

- Google (primary: Cloud Run, Gemini, ADK)
- NVIDIA (GPU acceleration)
- Vercel/Netlify (frontend hosting alternatives)
- Major AI/ML companies

**Sponsorship Tiers:**

| Tier                       | Monthly Contribution | Benefits                                                    |
| :------------------------- | :------------------- | :---------------------------------------------------------- |
| **Infrastructure Sponsor** | $500/month           | Logo on README, mention in docs, priority feature requests  |
| **GPU Sponsor**            | $300/month           | Logo on README, mention in GPU docs, dedicated GPU instance |
| **Cloud Sponsor**          | $200/month           | Logo on README, mention in deployment docs                  |
| **Community Sponsor**      | $100/month           | Logo on README footer                                       |
| **Supporter**              | $50/month            | Name in CONTRIBUTORS.md                                     |

**Approach:**

1. Prepare sponsorship prospectus (use this document as basis)
2. Identify developer relations contacts at target companies
3. Submit sponsorship proposals via official channels
4. Offer value: case study, blog post, conference presentation

---

### 2.4 Grant Programs

#### A. Google Open Source Programs

**Website:** https://opensource.google/documentation/reference/growing/funding

**Programs:**

- **Google Season of Docs:** $5,000-15,000 for documentation projects
- **Google Cloud Credits:** Up to $100,000 in Cloud credits (application required)
- **Open Source Peer Bonus:** $500 one-time awards for contributors

**Eligibility:** Open-source projects using Google technologies (✅ Cloud Run, Gemini, ADK)

**Application Process:**

1. Research specific program requirements
2. Prepare project proposal highlighting Google tech usage
3. Submit during open application periods
4. Follow up with program coordinators

**Likelihood:** **High** - Project extensively uses Google Cloud Platform and Gemini/Gemma models.

---

#### B. GitHub Accelerator

**Website:** https://accelerator.github.com

**Details:**

- $20,000 stipend for maintainers
- Mentorship and community support
- 10-week program
- Twice yearly cohorts

**Eligibility:**

- Open-source maintainers
- Active community
- Demonstrated impact

**Application:** Opens twice yearly (spring and fall).

---

#### C. Sovereign Tech Fund (STF)

**Website:** https://sovereigntechfund.de

**Details:**

- Focus: Digital infrastructure and security
- Funding: €5,000-250,000 per project
- Duration: 6-12 months
- Requirements: European focus (but international projects accepted)

**Eligibility:** Projects with public interest and infrastructure value.

---

#### D. Other Grant Opportunities

| Program                                | Amount          | Focus                     | Website                                |
| :------------------------------------- | :-------------- | :------------------------ | :------------------------------------- |
| **AWS Open Source Program**            | Varies          | AWS-based projects        | https://aws.amazon.com/opensource/     |
| **Microsoft FOSS Fund**                | $10,000         | Developer tools           | https://github.com/microsoft/foss-fund |
| **NLnet Foundation**                   | €5,000-50,000   | Privacy, security, search | https://nlnet.nl                       |
| **Mozilla Open Source Support (MOSS)** | $10,000-250,000 | Internet health           | https://www.mozilla.org/en-US/moss/    |
| **Python Software Foundation**         | $1,000-20,000   | Python projects           | https://www.python.org/psf/grants/     |

---

### 2.5 Community Crowdfunding

**Platforms:**

- **Buy Me a Coffee** (https://buymeacoffee.com) - Simple one-time donations
- **Ko-fi** (https://ko-fi.com) - One-time and recurring donations
- **Patreon** (https://patreon.com) - Subscription-based support

**Recommended:** Use GitHub Sponsors as primary, link Buy Me a Coffee for non-GitHub users.

---

### 2.6 Proposed GitHub Sponsors Tier Structure

| Tier Name                     | Monthly Amount | Benefits                                                                                                                                                            |
| :---------------------------- | :------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **☕ Coffee Sponsor**         | $5/month       | • Name in SUPPORTERS.md<br>• Sponsor badge on profile                                                                                                               |
| **🚀 Contributor Sponsor**    | $25/month      | • All Coffee benefits<br>• Early access to features<br>• Discord/Community access                                                                                   |
| **💎 Professional Sponsor**   | $100/month     | • All Contributor benefits<br>• Priority issue responses<br>• Name in README sponsors section                                                                       |
| **🏢 Corporate Sponsor**      | $500/month     | • All Professional benefits<br>• Logo in README (medium size)<br>• Quarterly roadmap consultation<br>• Dedicated support channel                                    |
| **🌟 Infrastructure Sponsor** | $1,000/month   | • All Corporate benefits<br>• Large logo in README and docs<br>• Monthly sync with maintainers<br>• Feature request priority<br>• Public acknowledgment in releases |

**One-Time Sponsorship:**

- $50 - Coffee pack (supporter acknowledgment)
- $250 - Feature sponsor (name in feature credits)
- $1,000 - Infrastructure contributor (special recognition)

---

## 3. Prioritized Funding Sources

Based on feasibility, timeline, and expected return:

### Priority 1: Immediate Actions (0-30 days)

1. **GitHub Sponsors Setup** ✅ Highest Priority
   - Expected revenue: $50-200/month initially
   - Timeline: 1 week to set up, 1-3 days for approval
   - Action: Complete application, create tiers, write profile
   - Effort: Low

2. **Google Cloud Credits Application** ✅ High Priority
   - Expected benefit: $100,000 in credits (covers 2+ years)
   - Timeline: 2-4 weeks for approval
   - Action: Submit application at https://cloud.google.com/developers/startups
   - Effort: Medium

3. **FUNDING.yml Creation** ✅ Immediate
   - Expected benefit: Discoverability
   - Timeline: Same day
   - Action: Create file and commit to repository
   - Effort: Low

### Priority 2: Short-Term Actions (1-3 months)

4. **GitHub Accelerator Application** ⚡ High Impact
   - Expected benefit: $20,000 stipend
   - Timeline: Next application window (spring/fall)
   - Action: Prepare application materials
   - Effort: Medium

5. **Corporate Sponsorship Outreach** 💼 High Potential
   - Expected revenue: $500-2,000/month if successful
   - Timeline: 2-6 months
   - Action: Prepare prospectus, identify contacts
   - Effort: High

6. **Buy Me a Coffee Setup** ☕ Quick Win
   - Expected revenue: $20-50/month
   - Timeline: 1 day
   - Action: Create account, link in README
   - Effort: Low

### Priority 3: Medium-Term Actions (3-6 months)

7. **Google Open Source Program Grants**
   - Expected benefit: $5,000-15,000
   - Timeline: Varies by program
   - Action: Monitor program announcements
   - Effort: Medium

8. **NLnet Foundation Grant**
   - Expected benefit: €10,000-50,000
   - Timeline: 4-6 months
   - Action: Prepare detailed proposal
   - Effort: High

9. **Python Software Foundation Grant**
   - Expected benefit: $5,000-10,000
   - Timeline: Quarterly application windows
   - Action: Emphasize Python/FastAPI components
   - Effort: Medium

---

## 4. Implementation Roadmap

### Phase 1: Foundation (Week 1-2) ✅ Current Phase

**Objectives:**

- Enable basic funding mechanisms
- Establish cost transparency
- Prepare for public launch

**Tasks:**

- [x] Create SUSTAINABILITY_PLAN.md
- [x] Create .github/FUNDING.yml
- [ ] Set up GitHub Sponsors profile
- [ ] Apply for Google Cloud credits
- [ ] Update README.md with sustainability section
- [ ] Announce funding options in CONTRIBUTING.md

**Deliverables:**

- FUNDING.yml committed to repository
- GitHub Sponsors application submitted
- Google Cloud credits application submitted
- Documentation updated

---

### Phase 2: Community Building (Month 1-3)

**Objectives:**

- Grow sponsor base
- Engage community
- Build credibility for grants

**Tasks:**

- [ ] Launch GitHub Sponsors (after approval)
- [ ] Write blog post about project sustainability
- [ ] Engage with potential sponsors on social media
- [ ] Create sponsor recognition system
- [ ] Prepare GitHub Accelerator application
- [ ] Set up Buy Me a Coffee backup option

**Deliverables:**

- Active GitHub Sponsors page
- 5-10 initial sponsors
- Sponsor recognition in README
- Grant applications submitted

---

### Phase 3: Growth & Grants (Month 3-6)

**Objectives:**

- Secure major funding
- Expand sponsor base
- Achieve cost coverage

**Tasks:**

- [ ] Submit GitHub Accelerator application
- [ ] Reach out to corporate sponsors
- [ ] Apply for NLnet Foundation grant
- [ ] Apply for PSF grant
- [ ] Write case studies for sponsors
- [ ] Present at conferences to attract sponsors

**Deliverables:**

- At least one major grant awarded
- 2-3 corporate sponsors secured
- 50+ individual sponsors
- 100% infrastructure cost coverage

---

### Phase 4: Sustainability (Month 6-12)

**Objectives:**

- Maintain funding momentum
- Expand project capabilities
- Support community growth

**Tasks:**

- [ ] Regular sponsor updates
- [ ] Quarterly financial transparency reports
- [ ] Apply for additional grants
- [ ] Expand tier benefits
- [ ] Hire part-time contributor (if funding allows)

**Deliverables:**

- Sustainable monthly funding
- Diversified funding sources
- Active community of contributors

---

## 5. Financial Transparency & Governance

### 5.1 Budget Allocation

**Proposed allocation of received funds:**

| Category                    | Percentage | Purpose                        |
| :-------------------------- | :--------- | :----------------------------- |
| **Infrastructure Costs**    | 60-70%     | Cloud Run, GPU, Firestore, GAR |
| **Development Bounties**    | 15-20%     | Community contributor rewards  |
| **Documentation & Content** | 5-10%      | Technical writing, tutorials   |
| **Community Management**    | 5-10%      | Events, swag, outreach         |
| **Emergency Reserve**       | 5-10%      | Buffer for unexpected costs    |

### 5.2 Transparency Commitments

**Quarterly Reports:**

- Total funds received (by source)
- Infrastructure costs breakdown
- Funds allocated to development
- Remaining balance
- Upcoming initiatives

**Public Dashboard:**

- Consider Open Collective for full transparency
- Publish quarterly summaries on GitHub Discussions
- Annual financial summary in README

### 5.3 Ethical Considerations

**Sponsor Acceptance Policy:**

- No sponsors with conflicting open-source values
- No sponsors engaged in harmful activities
- Maintain project independence
- Disclose all corporate relationships

---

## 6. Risk Mitigation

### 6.1 Funding Risks

| Risk                             | Probability | Impact | Mitigation                                               |
| :------------------------------- | :---------- | :----- | :------------------------------------------------------- |
| **Insufficient sponsorship**     | Medium      | High   | Multiple funding sources, cost optimization              |
| **Grant rejection**              | Medium      | Medium | Apply to multiple programs, diverse strategy             |
| **Corporate sponsor withdrawal** | Low         | High   | Never depend on single sponsor (max 30% from one source) |
| **Infrastructure cost spike**    | Low         | High   | Monitoring, alerts, scale-to-zero policies               |
| **Platform dependency (GitHub)** | Low         | Medium | Backup funding platforms (Open Collective)               |

### 6.2 Cost Control Strategies

**Immediate Actions:**

- ✅ Scale-to-zero configuration for all Cloud Run services
- ✅ GPU instance max limit set to 2
- ✅ Firestore read/write optimization

**Ongoing Monitoring:**

- Weekly Cloud Billing dashboard reviews
- Budget alerts at 50%, 75%, 90% of monthly target
- Automated cost anomaly detection

**Emergency Measures (if funding insufficient):**

- Reduce Gemma GPU max instances to 1
- Implement stricter rate limiting
- Consider smaller model (Gemma 2B vs 7B)
- Temporary service degradation vs shutdown

---

## 7. Communication Strategy

### 7.1 Sponsor Messaging

**Key Messages:**

- "Support cutting-edge AI agent research"
- "Enable GPU-accelerated open-source AI"
- "Make advanced knowledge exploration accessible to all"
- "Transparent, community-driven development"

**Value Proposition:**

- Real-world demonstration of Google Cloud Platform + ADK
- Active community and contributor base
- High-quality codebase and documentation
- Regular updates and feature releases

### 7.2 Where to Communicate

**Primary Channels:**

- GitHub README.md (prominent sustainability section)
- GitHub Sponsors profile
- Project website (if created)
- Twitter/X, LinkedIn, Mastodon

**Secondary Channels:**

- Dev.to blog posts
- Hacker News Show HN posts
- Reddit (r/opensource, r/MachineLearning)
- Conference presentations

### 7.3 Sponsor Recognition

**Tiers of Recognition:**

**Infrastructure Sponsors ($1000+/month):**

- Large logo in README header
- Dedicated page in docs/SPONSORS.md
- Monthly blog post acknowledgment
- Release notes mention

**Corporate Sponsors ($500/month):**

- Medium logo in README
- Name in docs/SPONSORS.md
- Quarterly acknowledgment

**Professional Sponsors ($100/month):**

- Name in README sponsors section
- Name in docs/SPONSORS.md

**Community Sponsors ($5-50/month):**

- Name in docs/SUPPORTERS.md
- GitHub sponsor badge

---

## 8. Success Metrics

### 8.1 Financial Metrics (Target: Month 12)

- **Total Monthly Recurring Revenue:** $500+ (covers 100% of infrastructure costs)
- **Number of Active Sponsors:** 50+
- **Corporate Sponsors:** 2-3
- **Grant Funding Received:** $20,000+
- **Average Sponsor Retention:** 80%+

### 8.2 Community Metrics

- **GitHub Stars:** 500+
- **Contributors:** 20+
- **Monthly Active Users:** 500+
- **Documentation Quality:** 90%+ positive feedback

### 8.3 Sustainability Metrics

- **Cost Coverage Ratio:** 100% (revenue >= costs)
- **Funding Source Diversity:** No single source > 30%
- **Reserve Fund:** 3 months of operating costs
- **Sponsor Satisfaction:** 90%+ would recommend

---

## 9. Alternative Scenarios

### 9.1 If Funding Falls Short

**Scenario:** Unable to secure sufficient sponsorship/grants

**Options:**

1. **Cost Reduction:**
   - Switch to Gemma 2B (smaller model, lower GPU costs)
   - Implement aggressive rate limiting
   - Reduce max GPU instances to 1
   - Target cost: $100-150/month (50% reduction)

2. **Service Tier Model:**
   - Free tier: Limited requests per day
   - Paid tier: Unlimited access ($5-10/month per user)
   - Enterprise tier: Dedicated instances ($50-100/month)

3. **Hybrid Model:**
   - Core features remain free
   - Premium features (advanced visualizations, custom agents) paid
   - Sponsor benefits expanded

### 9.2 If Funding Exceeds Expectations

**Scenario:** Receiving $1,000+ per month in sponsorship

**Opportunities:**

1. **Expand Infrastructure:**
   - Add more GPU instances
   - Implement caching layer (Redis)
   - Multi-region deployment for lower latency

2. **Accelerate Development:**
   - Hire part-time developer ($2,000-3,000/month)
   - Funded contributor program ($100-200 per major feature)
   - Bug bounty program ($50-500 per critical issue)

3. **Community Growth:**
   - Sponsor conference talks
   - Create video tutorials
   - Host virtual workshops
   - Swag for top contributors

---

## 10. Next Steps (Action Items)

### Immediate (This Week)

1. **Create FUNDING.yml** ✅ Priority 1
   - File location: `.github/FUNDING.yml`
   - Include GitHub Sponsors (when approved)
   - Action: Create file and commit

2. **Apply for GitHub Sponsors** ✅ Priority 1
   - URL: https://github.com/sponsors
   - Prepare sponsor profile text
   - Create tier structure (use section 2.6)
   - Action: Submit application

3. **Apply for Google Cloud Credits** ✅ Priority 1
   - URL: https://cloud.google.com/developers/startups
   - Emphasize use of Cloud Run, Gemini, ADK
   - Action: Submit application

4. **Update README.md** 🔄 Priority 2
   - Add sustainability section
   - Link to this document
   - Action: Edit README

### Short-Term (Next 2-4 Weeks)

5. **Set up Buy Me a Coffee** ☕
   - Backup option for non-GitHub users
   - Action: Create account, add to FUNDING.yml

6. **Prepare Corporate Sponsorship Materials**
   - Create one-page prospectus
   - Identify target companies
   - Action: Draft materials

7. **Monitor Grant Application Windows**
   - GitHub Accelerator (spring/fall)
   - Python Software Foundation (quarterly)
   - Action: Set calendar reminders

### Medium-Term (Next 1-3 Months)

8. **Submit Grant Applications**
   - GitHub Accelerator (next window)
   - NLnet Foundation
   - PSF Grant
   - Action: Complete applications

9. **Reach Out to Corporate Sponsors**
   - Google Developer Relations
   - NVIDIA Developer Programs
   - Action: Email outreach

10. **Create Sponsor Recognition System**
    - docs/SPONSORS.md
    - docs/SUPPORTERS.md
    - README badge system
    - Action: Implement system

---

## 11. Conclusion

The **Agentic Navigator** project requires approximately **$4,200-5,000 per year** to sustain active community usage. This funding will primarily cover GPU costs for the Gemma service, with additional infrastructure costs for Cloud Run, Firestore, and other GCP services.

**Recommended Strategy:**

1. **GitHub Sponsors** as primary recurring revenue source
2. **Google Cloud Credits** to reduce infrastructure costs
3. **Corporate Sponsorship** for major funding
4. **Grant Applications** for one-time funding boosts
5. **Cost Optimization** to minimize baseline expenses

**Key Success Factors:**

- ✅ Transparent budget and fund allocation
- ✅ Diverse funding sources (no single point of failure)
- ✅ Strong community engagement
- ✅ High-quality project execution
- ✅ Regular sponsor communication

With a proactive, multi-channel approach to sustainability, the project can secure the resources needed for long-term success while maintaining its open-source values and community focus.

**Status:** Ready for implementation. Next step: Create FUNDING.yml and submit GitHub Sponsors application.

---

**Document Prepared By:** Agentic Navigator Core Team  
**Review Cycle:** Quarterly  
**Next Review:** Q1 2026

---

## Appendix A: Useful Resources

**GitHub Sponsors:**

- Setup Guide: https://docs.github.com/en/sponsors/receiving-sponsorships-through-github-sponsors
- Pricing: https://github.com/pricing (no fees)
- Examples: https://github.com/sponsors/explore

**Google Cloud Platform:**

- Pricing Calculator: https://cloud.google.com/products/calculator
- Cloud Credits: https://cloud.google.com/developers/startups
- Open Source Programs: https://opensource.google/documentation/reference/growing/funding

**Grant Programs:**

- GitHub Accelerator: https://accelerator.github.com
- NLnet Foundation: https://nlnet.nl/propose/
- Python Software Foundation: https://www.python.org/psf/grants/
- Sovereign Tech Fund: https://sovereigntechfund.de/en/

**Alternative Funding:**

- Open Collective: https://opencollective.com
- Buy Me a Coffee: https://buymeacoffee.com
- Ko-fi: https://ko-fi.com

**Community Resources:**

- Open Source Guides: https://opensource.guide/
- Sustain OSS: https://sustainoss.org/
- FOSS Funding: https://fossfunding.com/

---

## Appendix B: Cost Estimation Methodology

**Data Sources:**

1. Terraform configuration (`terraform/cloud_run.tf`)
2. Google Cloud Pricing Calculator
3. Historical usage patterns (if available)
4. Industry benchmarks for similar projects

**Assumptions:**

- Cloud Run scale-to-zero enabled (min_instances=0)
- GPU usage: 50-100 hours/month for active community
- Firestore: 100K reads, 20K writes per month
- Container image storage: 10GB
- Network egress: 100GB/month
- CI/CD builds: 20 builds/month

**Pricing References (as of November 2025):**

- Cloud Run (CPU): $0.00002400/vCPU-second
- Cloud Run (Memory): $0.00000250/GiB-second
- Cloud Run (GPU L4): ~$1.50-2.00/hour
- Firestore: $0.06 per 100K reads, $0.18 per 100K writes
- GAR Storage: $0.10/GiB/month

**Note:** Cloud pricing changes frequently. Always verify current pricing at https://cloud.google.com/pricing before making budget decisions.

---

_End of Sustainability Plan_
