/**
 * Enhanced Booking UI.
 * - Gender tabs for available wrestlers
 * - Drag & drop into match slots
 * - Match type / importance / stipulation / championship / winner mode
 * - Story suggestion
 * - Validation before submit
 */

(function () {
    "use strict";

    const slotEls = document.querySelectorAll(".match-slot");
    const pool = document.getElementById("roster-pool");
    const form = document.getElementById("booking-form");
    const cardInput = document.getElementById("card_json");
    const segmentsInput = document.getElementById("segments_json");
    const segmentBuilder = document.getElementById("segment-builder");
    const segmentList = document.getElementById("segment-list");
    let segments = segmentBuilder
        ? JSON.parse(segmentBuilder.dataset.existingSegments || "[]")
        : [];

    // ✅ FIX: set width via JS instead of inline style with %
    document.querySelectorAll(".story-progress-fill").forEach((bar) => {
        const progress = bar.dataset.progress || 0;
        bar.style.width = progress + "%";
    });

    let dragged = null;

    // Restore visual state for cards loaded from the session.
    slotEls.forEach((slot) => updateSlotState(slot));

    // =====================================================
    // GENDER TABS
    // =====================================================
    document.querySelectorAll(".tab-btn").forEach((tab) => {
        tab.addEventListener("click", () => {
            const gender = tab.dataset.gender;

            document.querySelectorAll(".tab-btn").forEach((t) =>
                t.classList.remove("active")
            );
            tab.classList.add("active");

            pool.querySelectorAll(".wrestler-chip").forEach((chip) => {
                const isFemale = chip.classList.contains("gender-female");
                if (gender === "FEMALE") {
                    chip.style.display = isFemale ? "" : "none";
                } else {
                    chip.style.display = isFemale ? "none" : "";
                }
            });

            pool.dataset.activeGender = gender;
        });
    });

    // =====================================================
    // DRAG START
    // =====================================================
    document.addEventListener("dragstart", (e) => {
        const chip = e.target.closest(".wrestler-chip");
        if (!chip) return;

        dragged = {
            id: chip.dataset.wrestlerId,
            name: chip.dataset.wrestlerName,
            gender: chip.dataset.gender,
            fromSlot: chip.closest(".match-slot")?.dataset.slotIndex ?? null,
        };

        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", dragged.id);
    });

    document.addEventListener("dragend", () => {
        dragged = null;
        document.querySelectorAll(".drop-zone").forEach((z) =>
            z.classList.remove("dragover")
        );
    });

    // =====================================================
    // DROP ZONES
    // =====================================================
    document.addEventListener("dragover", (e) => {
        const zone = e.target.closest(".drop-zone");
        if (zone) {
            e.preventDefault();
            zone.classList.add("dragover");
        }
    });

    document.addEventListener("dragleave", (e) => {
        const zone = e.target.closest(".drop-zone");
        if (zone) zone.classList.remove("dragover");
    });

    document.addEventListener("drop", (e) => {
        const zone = e.target.closest(".drop-zone");
        if (!zone) return;
        e.preventDefault();
        zone.classList.remove("dragover");
        if (!dragged) return;

        const slot = zone.closest(".match-slot");

        if (
            dragged.fromSlot !== null &&
            dragged.fromSlot !== slot.dataset.slotIndex
        ) {
            const oldZone = document.querySelector(
                `.match-slot[data-slot-index="${dragged.fromSlot}"] .drop-zone`
            );
            if (oldZone) {
                const oldChip = oldZone.querySelector(
                    `[data-wrestler-id="${dragged.id}"]`
                );
                if (oldChip) {
                    oldChip.remove();
                    updateSlotState(oldZone.closest(".match-slot"));
                }
            }
        }

        if (zone.querySelector(`[data-wrestler-id="${dragged.id}"]`)) {
            return;
        }

        const existingChips = zone.querySelectorAll(".wrestler-chip");
        for (const chip of existingChips) {
            if (chip.dataset.gender !== dragged.gender) {
                alert("لا يمكن خلط الجنسين في نفس المباراة.");
                return;
            }
        }

        const chip = document.createElement("span");
        chip.className = "wrestler-chip small";
        chip.draggable = true;
        chip.dataset.wrestlerId = dragged.id;
        chip.dataset.wrestlerName = dragged.name;
        chip.dataset.gender = dragged.gender;
        chip.textContent = dragged.name;

        const hint = zone.querySelector(".drop-hint");
        if (hint) hint.remove();

        zone.appendChild(chip);
        updateSlotState(slot);
    });

    // =====================================================
    // CLEAR SLOT
    // =====================================================
    document.addEventListener("click", (e) => {
        if (e.target.classList.contains("clear-slot-btn")) {
            const slot = e.target.closest(".match-slot");
            const zone = slot.querySelector(".drop-zone");
            zone.innerHTML = '<span class="drop-hint">اسحب المصارعين إلى هنا</span>';
            updateSlotState(slot);

            const override = slot.querySelector(".slot-winner-override");
            override.innerHTML = '<option value="">— اختر الفائز —</option>';
        }
    });

    // =====================================================
    // WINNER MODE TOGGLE
    // =====================================================
    document.addEventListener("change", (e) => {
        if (e.target.classList.contains("slot-winner-mode")) {
            const slot = e.target.closest(".match-slot");
            const override = slot.querySelector(".slot-winner-override");
            if (e.target.value === "MANUAL") {
                override.style.display = "";
                refreshWinnerOptions(slot);
            } else {
                override.style.display = "none";
            }
        }
    });

    // =====================================================
    // SLOT STATE
    // =====================================================
    function updateSlotState(slot) {
        const zone = slot.querySelector(".drop-zone");
        const chips = zone.querySelectorAll(".wrestler-chip");
        const count = chips.length;

        slot.classList.toggle("filled", count >= 2);
        slot.classList.toggle("partial", count === 1);

        const status = slot.querySelector(".slot-status");
        if (count === 0) status.textContent = "فارغ";
        else if (count === 1) status.textContent = "مصارع واحد";
        else status.textContent = `${count} مصارعين`;

        const mode = slot.querySelector(".slot-winner-mode").value;
        if (mode === "MANUAL") {
            refreshWinnerOptions(slot);
        }
        renderRundown();
    }

    function refreshWinnerOptions(slot) {
        const override = slot.querySelector(".slot-winner-override");
        const chips = slot.querySelectorAll(".drop-zone .wrestler-chip");
        const currentVal = override.value;

        override.innerHTML = '<option value="">— اختر الفائز —</option>';
        chips.forEach((chip) => {
            const opt = document.createElement("option");
            opt.value = chip.dataset.wrestlerId;
            opt.textContent = chip.dataset.wrestlerName;
            if (opt.value === currentVal) opt.selected = true;
            override.appendChild(opt);
        });
    }

    // =====================================================
    // SUBMIT
    // =====================================================
    form.addEventListener("submit", (e) => {
        const card = buildCardJson();
        if (card.length === 0) {
            e.preventDefault();
            alert("احجز مباراة واحدة على الأقل أولًا.");
            return;
        }

        for (const entry of card) {
            if (entry.winner_mode === "MANUAL" && !entry.winner_override_id) {
                e.preventDefault();
                alert("اختر فائزًا لكل مباراة يدوية أو أعدها إلى تلقائي.");
                return;
            }
        }

        cardInput.value = JSON.stringify(card);
        segmentsInput.value = JSON.stringify(segments);
    });

    // =====================================================
    // SEGMENTS
    // =====================================================
    function renderSegments() {
        if (!segmentList) return;
        segmentList.innerHTML = "";
        if (!segments.length) {
            segmentList.innerHTML =
                '<span class="segment-empty">لم تتم إضافة فقرات بعد.</span>';
            renderRundown();
            return;
        }
        segments.forEach((segment, index) => {
            const row = document.createElement("div");
            row.className = "segment-row";
            const names =
                segment.participant_names || segment.participant_ids.join(" + ");
            row.innerHTML = `
                <div>
                    <span class="segment-type">${segment.type.replaceAll("_", " ")}</span>
                    <strong>${names}</strong>
                    ${segment.story_title ? `<small> · ${segment.story_title}</small>` : ""}
                </div>
                <button type="button" class="btn tiny danger" data-remove-segment="${index}">مسح</button>
            `;
            segmentList.appendChild(row);
        });
        const count = document.querySelector(".segment-heading h3 .muted");
        if (count)
            count.textContent = `(${segments.length}/${segmentBuilder.dataset.limit || "?"})`;
        renderRundown();
    }

    function renderRundown() {
        const list = document.getElementById("rundown-list");
        if (!list) return;
        list.innerHTML = "";
        const typeLabels = {
            PROMO: "برومو",
            CALLOUT: "استفزاز",
            BACKSTAGE_ATTACK: "هجوم خلف الكواليس",
            INTERFERENCE: "تدخل",
            CONTRACT_SIGNING: "توقيع عقد",
            CELEBRATION: "احتفال",
        };
        const slots = document.querySelectorAll(".match-slot");
        for (let position = 0; position <= slots.length; position += 1) {
            segments
                .filter((segment) => Number(segment.position || 0) === position)
                .forEach((segment) => {
                    const item = document.createElement("div");
                    item.className = "rundown-item segment-item";
                    item.innerHTML = `<span class="rundown-index">${
                        list.children.length + 1
                    }</span><span>🎙️ ${typeLabels[segment.type] || segment.type}</span>`;
                    list.appendChild(item);
                });
            if (position < slots.length) {
                const count = slots[position].querySelectorAll(
                    ".drop-zone .wrestler-chip"
                ).length;
                const item = document.createElement("div");
                item.className = `rundown-item ${
                    count >= 2 ? "match-ready" : "match-empty"
                }`;
                item.innerHTML = `<span class="rundown-index">${
                    list.children.length + 1
                }</span><span>🎬 مباراة ${position + 1}</span><small>${
                    count >= 2 ? "جاهزة" : "فارغة"
                }</small>`;
                list.appendChild(item);
            }
        }
    }

    if (segmentBuilder) {
        segmentBuilder.dataset.limit = segmentBuilder.dataset.limit || "";
        renderSegments();
        document
            .getElementById("add-segment-btn")
            .addEventListener("click", () => {
                const type = document.getElementById("segment-type").value;
                const actor = document.getElementById("segment-actor");
                const target = document.getElementById("segment-target");
                const story = document.getElementById("segment-story");
                const position = document.getElementById("segment-position");
                if (!actor.value) {
                    alert("اختر المصارع الرئيسي للفقرة.");
                    return;
                }
                const ids = [actor.value];
                const names = [actor.options[actor.selectedIndex].text];
                if (target.value && target.value !== actor.value) {
                    ids.push(target.value);
                    names.push(target.options[target.selectedIndex].text);
                }
                segments.push({
                    type,
                    participant_ids: ids,
                    participant_names: names.join(" + "),
                    story_id: story.value || null,
                    story_title: story.value
                        ? story.options[story.selectedIndex].text
                        : "",
                    position: Number(position.value || 0),
                });
                renderSegments();
                actor.value = "";
                target.value = "";
                story.value = "";
                position.value = "0";
            });
        segmentList.addEventListener("click", (event) => {
            const button = event.target.closest("[data-remove-segment]");
            if (!button) return;
            segments.splice(Number(button.dataset.removeSegment), 1);
            renderSegments();
        });
    }

    function buildCardJson() {
        const result = [];
        document.querySelectorAll(".match-slot").forEach((slot) => {
            const chips = slot.querySelectorAll(".drop-zone .wrestler-chip");
            if (chips.length < 2) return;

            const participantIds = Array.from(chips).map(
                (c) => c.dataset.wrestlerId
            );

            const matchType = slot.querySelector(".slot-type").value;
            const importance = slot.querySelector(".slot-importance").value;
            const stipulation = slot.querySelector(".slot-stipulation").value;
            const championshipId =
                slot.querySelector(".slot-championship").value || null;
            const winnerMode = slot.querySelector(".slot-winner-mode").value;
            const winnerOverrideId =
                slot.querySelector(".slot-winner-override").value || null;
            const storyId = slot.querySelector(".slot-story").value || null;

            let finalMatchType = matchType;
            if (championshipId && matchType !== "CHAMPIONSHIP") {
                finalMatchType = "CHAMPIONSHIP";
            }

            result.push({
                participant_ids: participantIds,
                match_type: finalMatchType,
                importance: importance,
                stipulation: stipulation,
                championship_id: championshipId,
                winner_mode: winnerMode,
                winner_override_id:
                    winnerMode === "MANUAL" ? winnerOverrideId : null,
                story_id: storyId,
            });
        });
        return result;
    }

    // =====================================================
    // SUGGEST MATCH FROM STORY
    // =====================================================
    document.querySelectorAll(".suggest-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const storyId = btn.dataset.storyId;
            fetch(`/api/story/${storyId}/suggest`)
                .then((r) => r.json())
                .then((data) => {
                    if (!data.participant_ids) return;

                    const emptySlot = Array.from(slotEls).find(
                        (s) =>
                            s.querySelectorAll(".drop-zone .wrestler-chip")
                                .length === 0
                    );
                    if (!emptySlot) {
                        alert("لا توجد أماكن مباريات فارغة.");
                        return;
                    }

                    const zone = emptySlot.querySelector(".drop-zone");
                    zone.innerHTML = "";

                    data.participant_ids.forEach((pid) => {
                        const chipData = document.querySelector(
                            `[data-wrestler-id="${pid}"]`
                        );
                        if (!chipData) return;

                        const chip = document.createElement("span");
                        chip.className = "wrestler-chip small";
                        chip.draggable = true;
                        chip.dataset.wrestlerId = pid;
                        chip.dataset.wrestlerName = chipData.dataset.wrestlerName;
                        chip.dataset.gender = chipData.dataset.gender;
                        chip.textContent = chipData.dataset.wrestlerName;
                        zone.appendChild(chip);
                    });

                    if (data.match_type) {
                        emptySlot.querySelector(".slot-type").value =
                            data.match_type;
                    }
                    if (data.importance) {
                        emptySlot.querySelector(".slot-importance").value =
                            data.importance;
                    }

                    const storySelect = emptySlot.querySelector(".slot-story");
                    if (storySelect) storySelect.value = storyId;
                    if (data.championship_id) {
                        emptySlot.querySelector(".slot-championship").value =
                            data.championship_id;
                    }

                    updateSlotState(emptySlot);
                    emptySlot.scrollIntoView({
                        behavior: "smooth",
                        block: "center",
                    });
                })
                .catch((err) => {
                    console.error(err);
                    alert("تعذر جلب اقتراح القصة.");
                });
        });
    })();
})();