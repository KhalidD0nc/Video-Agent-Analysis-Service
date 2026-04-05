# CoachAI Analysis Report
**Video:** downloaded_match_clip.mp4  
**Total Pipeline Time:** 160.9s

---

## ⏱ Pipeline Timings

| Stage | Duration |
|---|---|
| Download | 0.1s |
| Inference | 91.4s |
| Cleaning | 0.7s → 93 events kept |
| Gemini Analysis | 68.7s |

**Events per model:**
- SoccerNet_small: 14 raw events
- SoccerNetBall_challenge1: 106 raw events

---

## 📋 Event Timeline

| Time | Event | Confidence | Type |
|---|---|---|---|
| `00:21` | 🤾 THROW IN | 0.71 | Ball Action |
| `00:31` | 🤾 THROW IN | 0.35 | Ball Action |
| `00:31` | • PASS | 0.84 | Ball Action |
| `00:34` | • DRIVE | 0.97 | Ball Action |
| `00:35` | • PASS | 0.77 | Ball Action |
| `00:39` | • OUT | 0.72 | Ball Action |
| `00:44` | • PASS | 0.79 | Ball Action |
| `00:45` | • DRIVE | 0.41 | Ball Action |
| `00:46` | 🥅 SHOT | 0.68 | Ball Action |
| `00:49` | • DRIVE | 0.31 | Ball Action |
| `00:52` | • PASS | 0.7 | Ball Action |
| `00:57` | 🎯 CROSS | 0.85 | Ball Action |
| `00:58` | 🤛 HEADER | 0.33 | Ball Action |
| `01:01` | 🤛 HEADER | 0.32 | Ball Action |
| `01:04` | • PASS | 0.57 | Ball Action |
| `01:06` | 🥅 SHOT | 0.95 | Ball Action |
| `01:07` | ⚽ GOAL | 0.37 | Ball Action |
| `01:07` | • DRIVE | 0.53 | Ball Action |
| `01:08` | • PASS | 0.95 | Ball Action |
| `01:11` | • DRIVE | 0.67 | Ball Action |
| `01:13` | • HIGH PASS | 0.31 | Ball Action |
| `01:13` | • PASS | 0.41 | Ball Action |
| `01:19` | • DRIVE | 0.75 | Ball Action |
| `01:20` | • PASS | 0.73 | Ball Action |
| `01:30` | • HIGH PASS | 0.59 | Ball Action |
| `01:32` | • PASS | 0.43 | Ball Action |
| `01:36` | 🥅 SHOT | 0.95 | Ball Action |
| `01:37` | • BALL PLAYER BLOCK | 0.33 | Ball Action |
| `01:37` | • DRIVE | 0.72 | Ball Action |
| `01:39` | 🎯 CROSS | 0.35 | Ball Action |
| `01:39` | • PASS | 0.38 | Ball Action |
| `01:41` | • DRIVE | 0.54 | Ball Action |
| `01:46` | 🥅 SHOT | 0.93 | Ball Action |
| `01:46` | • BALL PLAYER BLOCK | 0.43 | Ball Action |
| `01:47` | ⚽ GOAL | 0.77 | Ball Action |
| `01:48` | • Ball out of play | 0.51 | Match Event |
| `02:00` | • HIGH PASS | 0.53 | Ball Action |
| `02:02` | 🥅 SHOT | 0.33 | Ball Action |
| `02:04` | • DRIVE | 0.79 | Ball Action |
| `02:05` | • PASS | 0.92 | Ball Action |
| `02:06` | 🥅 SHOT | 0.98 | Ball Action |
| `02:07` | • OUT | 0.64 | Ball Action |
| `02:15` | • Clearance | 0.38 | Match Event |
| `02:15` | • HIGH PASS | 0.53 | Ball Action |
| `02:16` | • PASS | 0.32 | Ball Action |
| `02:18` | 🥅 SHOT | 0.45 | Ball Action |
| `02:20` | • OUT | 0.32 | Ball Action |
| `02:24` | • HIGH PASS | 0.43 | Ball Action |
| `02:27` | • PASS | 0.51 | Ball Action |
| `02:31` | • PASS | 0.61 | Ball Action |
| `02:32` | • DRIVE | 0.66 | Ball Action |
| `02:33` | 🥅 SHOT | 0.87 | Ball Action |
| `02:38` | • OUT | 0.53 | Ball Action |
| `02:44` | • HIGH PASS | 0.37 | Ball Action |
| `02:46` | • Throw-in | 0.33 | Match Event |
| `02:49` | • DRIVE | 0.46 | Ball Action |
| `02:50` | 🥅 SHOT | 0.69 | Ball Action |
| `02:50` | • BALL PLAYER BLOCK | 0.44 | Ball Action |
| `02:50` | • Ball out of play | 0.33 | Match Event |
| `02:51` | • OUT | 0.56 | Ball Action |
| `03:07` | • Throw-in | 0.33 | Match Event |
| `03:13` | • PASS | 0.95 | Ball Action |
| `03:14` | • DRIVE | 0.72 | Ball Action |
| `03:17` | 🥅 SHOT | 0.76 | Ball Action |
| `03:17` | • BALL PLAYER BLOCK | 0.58 | Ball Action |
| `03:18` | • Ball out of play | 0.82 | Match Event |
| `03:28` | • DRIVE | 0.57 | Ball Action |
| `03:29` | • PASS | 0.62 | Ball Action |
| `03:38` | 🎯 CROSS | 0.6 | Ball Action |
| `03:40` | • HIGH PASS | 0.38 | Ball Action |
| `03:48` | 🟡 Foul | 0.42 | Match Event |
| `03:48` | • HIGH PASS | 0.31 | Ball Action |
| `03:55` | 📐 Corner | 0.8 | Match Event |
| `03:55` | 🎯 CROSS | 0.44 | Ball Action |
| `03:56` | 🥅 SHOT | 0.62 | Ball Action |
| `03:58` | 🤛 HEADER | 0.47 | Ball Action |
| `03:59` | • Ball out of play | 0.36 | Match Event |
| `04:01` | • DRIVE | 0.32 | Ball Action |
| `04:05` | • OUT | 0.57 | Ball Action |
| `04:09` | 🎯 FREE KICK | 0.56 | Ball Action |
| `04:09` | 🥅 SHOT | 0.96 | Ball Action |
| `04:11` | ⚽ GOAL | 0.64 | Ball Action |
| `04:16` | 🤾 THROW IN | 0.6 | Ball Action |
| `04:20` | • DRIVE | 0.98 | Ball Action |
| `04:22` | • PASS | 0.97 | Ball Action |
| `04:23` | 🥅 SHOT | 0.99 | Ball Action |
| `04:25` | • Ball out of play | 0.33 | Match Event |
| `04:26` | • OUT | 0.53 | Ball Action |
| `04:35` | 🔁 Substitution | 0.34 | Match Event |
| `04:35` | 🤾 THROW IN | 0.33 | Ball Action |
| `04:37` | 🔄 Kick-off | 0.38 | Match Event |
| `04:42` | 🔄 Kick-off | 0.6 | Match Event |
| `04:57` | • HIGH PASS | 0.32 | Ball Action |

---

## 🧠 Tactical Phases

### Phase 1: Attacking Transition `00:44 → 01:07`

| | |
|---|---|
| **Zone** | Final Third - Wide Right |
| **Event** | Cross and Finish |
| **Attack Rating** | `████████░░` 8/10 |
| **Defense Rating** | `████░░░░░░` 4/10 |

**🔍 Tactical Breakdown**  
Abha executes a rapid vertical transition, exploiting space behind the Al-Jubail wing-backs. A high-quality cross is delivered from the wide right channel into the 'corridor of uncertainty'. The Al-Jubail defensive line remains static, allowing Abha attackers to win the initial aerial duel and recycle the second ball for a close-range finish. The Yellow team's recovery runs were disjointed, failing to provide cover for the center-backs.

**💡 Key Insight**  
Late arrivals into the penalty area are often untracked when the defensive block is preoccupied with the flight of a wide delivery.

**📋 Coach Advice**  
Focus on the 'Ball-Man' scanning technique for defenders during crosses; center-backs must communicate to identify runners entering the six-yard box.

**🏃 Training Drill**  
Crossing and Finishing under Pressure: 4v3 in the box with rotating wide deliveries.

---
### Phase 2: Sustained Pressure `01:30 → 01:48`

| | |
|---|---|
| **Zone** | Zone 14 / Penalty Area |
| **Event** | Goal |
| **Attack Rating** | `█████████░` 9/10 |
| **Defense Rating** | `███░░░░░░░` 3/10 |

**🔍 Tactical Breakdown**  
Abha maintains high-intensity pressure following a partially cleared set-piece. They utilize quick, short combinations in Zone 14 to pull the Al-Jubail defensive block out of position. A blocked shot is immediately recovered by the Abha midfield (Counter-press), leading to a secondary penetration on the left flank. A low, driven ball across the face of the goal finds a clinical finish at the back post.

**💡 Key Insight**  
The efficiency of the counter-press immediately following a blocked shot is the primary catalyst for this goal.

**📋 Coach Advice**  
Implement a '3-second rule' for ball recovery in the final third to capitalize on the defensive disorganization inherent in 'second-ball' scenarios.

**🏃 Training Drill**  
Rondo Transition: 5v2 transitioning into a 5v5 goal-scoring game upon possession loss/gain.

---
### Phase 3: Direct Build-up `02:15 → 02:38`

| | |
|---|---|
| **Zone** | Middle Third to Final Third - Central |
| **Event** | Long Ball and Shot |
| **Attack Rating** | `███████░░░` 7/10 |
| **Defense Rating** | `█████░░░░░` 5/10 |

**🔍 Tactical Breakdown**  
Abha utilizes a direct approach, bypassing the Al-Jubail midfield press with a high pass into the striker. The attacking unit successfully wins the flick-on, facilitating a 'third-man run' from deep. Al-Jubail's backline is caught flat-footed, allowing a shot from the edge of the area. The defensive transition from Jubail lacks depth, leaving huge gaps between the defensive and midfield lines.

**💡 Key Insight**  
Direct verticality can dismantle a high-pressing team if their defensive line fails to drop in anticipation of the long delivery.

**📋 Coach Advice**  
Train center-backs to 'read the body language' of the opposing kicker to trigger a proactive drop or step-up.

**🏃 Training Drill**  
Vertical Penetration Games: 8v8 focusing on direct passes into target forwards with supporting runs.

---
### Phase 4: Offensive Set Piece `03:55 → 04:05`

| | |
|---|---|
| **Zone** | Penalty Area |
| **Event** | Corner Kick |
| **Attack Rating** | `████████░░` 8/10 |
| **Defense Rating** | `████░░░░░░` 4/10 |

**🔍 Tactical Breakdown**  
Abha employs an inswinging delivery targeting the near-post area. They use blockers to obstruct Al-Jubail's primary zonal markers, creating a free path for their target man. The Yellow team relies heavily on a static zonal marking system which is easily exploited by the dynamic movement of the Navy attackers. A powerful header results from the lack of physical engagement by the defenders.

**💡 Key Insight**  
Zonal marking systems are vulnerable to 'blocker' movements that prevent defenders from jumping or tracking runs.

**📋 Coach Advice**  
Incorporate man-marking for the opponent's three best aerial threats within the zonal scheme to ensure physical contact.

**🏃 Training Drill**  
Set Piece Specialization: 6v6 Corner Defense focusing on aggressive man-to-man contact.

---
### Phase 5: Offensive Set Piece `04:09 → 04:11`

| | |
|---|---|
| **Zone** | Final Third - Central |
| **Event** | Direct Free Kick Goal |
| **Attack Rating** | `██████████` 10/10 |
| **Defense Rating** | `██░░░░░░░░` 2/10 |

**🔍 Tactical Breakdown**  
A direct free kick from roughly 22 yards out. Abha's specialist identifies a weakness in the Al-Jubail wall, which appears to have a slight gap between the second and third man. The strike is precise, curling over the wall and dipping into the corner. The goalkeeper's starting position was marginally too central, making it impossible to reach the ball despite a late dive.

**💡 Key Insight**  
Wall structural integrity is paramount; a single inch of separation can be the difference between a block and a goal at the professional level.

**📋 Coach Advice**  
Standardize wall communication; the goalkeeper must lead the alignment from the post to ensure no gaps are present.

**🏃 Training Drill**  
Set Piece Simulation: Direct free kick practice with defenders in a wall using mannequins and active players.

---

## 📝 Full Coaching Report

### Comprehensive Tactical Analysis (Abha vs. Al-Jubail)

Abha (Navy) displayed a dominant performance characterized by clinical verticality and superior organization during transitions, effectively dismantling Al-Jubail's (Yellow) defensive block. Al-Jubail struggled significantly with defensive communication and the management of second-ball scenarios, leading to multiple high-quality scoring opportunities for the opposition.

#### 1. Attacking Transition: Exploiting Wide Channels
* **What the data says:** Between 00:44 and 01:07, Abha initiated a rapid vertical transition. The sequence involved a driving run and a high-quality cross from the wide right channel (00:57), followed by two successive headers and a close-range shot that resulted in a goal at 01:07.
* **Diagnosis:** Abha successfully exploited the space behind Al-Jubail's wing-backs. The Al-Jubail defensive line remained static during the cross, failing to track runners in the "corridor of uncertainty." Disjointed recovery runs left the center-backs isolated against late-arriving attackers.
* **Tactical Advice:** Defenders must prioritize the "Ball-Man" scanning technique during wide deliveries. Center-backs must lead communication to identify and pick up late runners entering the six-yard box, ensuring no attacker is left unmarked while the block is focused on the flight of the ball.

#### 2. Sustained Pressure and Final Third Counter-Pressing
* **What the data says:** From 01:30 to 01:48, Abha maintained high intensity in Zone 14. After a shot was blocked (01:37), Abha immediately recovered possession through a counter-press, leading to a driven ball across the face of the goal and a back-post finish (01:47).
* **Diagnosis:** The goal was a direct result of Abha's efficient counter-press. Al-Jubail’s defensive block was pulled out of position by quick short combinations and failed to reset quickly enough after the initial clearance, leaving the back post vulnerable.
* **Tactical Advice:** Implement a strict "3-second rule" for ball recovery in the final third. Capitalizing on the inherent disorganization of the defense immediately following a blocked shot or partial clearance is a high-percentage scoring strategy.

#### 3. Direct Build-up and Vertical Penetration
* **What the data says:** At 02:15, Abha bypassed the midfield press with a direct high pass. A successful flick-on led to a "third-man run" and a shot from the edge of the area at 02:33, demonstrating a highly efficient bypass of the Al-Jubail lines.
* **Diagnosis:** Al-Jubail's backline was caught flat-footed. Because the defensive line failed to drop in anticipation of the long delivery, Abha was able to exploit the massive gaps created between Jubail's defensive and midfield units.
* **Tactical Advice:** Center-backs must be trained to "read the body language" of the opposing kicker. Any sign of a long, vertical delivery should trigger a proactive drop of the defensive line to eliminate space for runners behind them.

#### 4. Offensive Set Piece: Near-Post Corner Tactics
* **What the data says:** Between 03:55 and 04:05, Abha executed an inswinging corner kick. A target man won a powerful header (03:58) due to a lack of physical engagement from the defenders, nearly resulting in another goal.
* **Diagnosis:** Al-Jubail relied on a static zonal marking system that was easily manipulated by Abha's use of "blockers." By obstructing zonal markers, Abha created a free path for their primary aerial threat.
* **Tactical Advice:** Integrate specific man-marking for the opponent's three most dangerous aerial threats within the existing zonal scheme. Ensuring physical contact and disrupting the run of these targets is vital to defending dynamic set-piece movements.

#### 5. Offensive Set Piece: Direct Free Kick Execution
* **What the data says:** At 04:09, Abha won a free kick roughly 22 yards from goal. The specialist identified a structural flaw and curled the ball over the wall into the corner (04:11) with extreme precision.
* **Diagnosis:** The goal resulted from a gap in the Al-Jubail wall between the second and third man. Furthermore, the goalkeeper's starting position was slightly too central, preventing a successful save despite a late attempt.
* **Tactical Advice:** Wall structural integrity is paramount. Communication must be standardized; the goalkeeper must lead the alignment from the post to ensure no gaps exist, as even a few inches of separation can be fatal at the professional level.

---

### Training Tips for the Coach (Based on Data Analysis)

**1. Drill: "Crossing and Finishing under Pressure"**
* **Objective:** Improves "Ball-Man" scanning and defensive communication during wide deliveries.
* **The Drill:** Set up a 4v3 scenario in the penalty area. Wide players rotate delivering crosses into the box while defenders practice identifying runners and communicating marking responsibilities under active pressure.

**2. Drill: "Rondo Transition (5v2 to 5v5)"**
* **Objective:** Enhances the efficiency of the counter-press and capitalizing on defensive disorganization.
* **The Drill:** Start with a 5v2 Rondo in a confined space. Upon a change of possession, the game expands into a 5v5 goal-scoring game on a half-pitch, emphasizing immediate ball recovery and rapid exploitation of the secondary transition.

**3. Drill: "Vertical Penetration Games"**
* **Objective:** Refines direct build-up play and supporting runs into the final third.
* **The Drill:** Run an 8v8 game where teams are encouraged to play direct passes into target forwards. Focus on the timing of "third-man runs" and the movement of the defensive line in response to long deliveries.

**4. Drill: "Set Piece Specialization (6v6 Corner Defense)"**
* **Objective:** Counteracts "blocker" movements and improves physical engagement in zonal marking.
* **The Drill:** Practice 6v6 corner situations where the attacking team specifically uses blockers. Defenders must practice navigating these blocks to maintain contact with their assigned targets or zones.

**5. Drill: "Set Piece Simulation (Wall Integrity)"**
* **Objective:** Standardizes wall alignment and goalkeeper communication.
* **The Drill:** Conduct direct free kick practice using a mix of mannequins and active players in the wall. The goalkeeper must practice directing the wall's alignment from the post to ensure total coverage and structural integrity.