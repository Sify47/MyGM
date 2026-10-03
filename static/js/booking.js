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

    let dragged = null;

    // Restore visual state for cards loaded from the session.
    slotEls.forEach((slot) => updateSlotState(slot));

    // =====================================================
    // GENDER TABS
    // =====================================================
    document.querySelectorAll(".tab-btn").forEach((tab) => {
        tab.addEventListener("click", () => {
            const gender = tab.dataset.gender;

            // Update active tab
            document.querySelectorAll(".tab-btn").forEach((t) =>
                t.classList.remove("active")
            );
            tab.classList.add("active");

            // Show/hide chips by gender
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

        // Remove from old slot if applicable
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

        // Prevent duplicate in same slot
        if (zone.querySelector(`[data-wrestler-id="${dragged.id}"]`)) {
            return;
        }

        // Gender consistency check
        const existingChips = zone.querySelectorAll(".wrestler-chip");
        for (const chip of existingChips) {
            if (chip.dataset.gender !== dragged.gender) {
                alert("Cannot mix genders in the same match.");
                return;
            }
        }

        // Add chip
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
            zone.innerHTML = '<span class="drop-hint">Drag wrestlers here</span>';
            updateSlotState(slot);

            // Reset winner override
            const override = slot.querySelector(".slot-winner-override");
            override.innerHTML = '<option value="">— Select Winner —</option>';
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
        if (count === 0) status.textContent = "Empty";
        else if (count === 1) status.textContent = "1 wrestler";
        else status.textContent = `${count} wrestlers`;

        // Refresh winner options if manual mode
        const mode = slot.querySelector(".slot-winner-mode").value;
        if (mode === "MANUAL") {
            refreshWinnerOptions(slot);
        }
    }

    function refreshWinnerOptions(slot) {
        const override = slot.querySelector(".slot-winner-override");
        const chips = slot.querySelectorAll(".drop-zone .wrestler-chip");
        const currentVal = override.value;

        override.innerHTML = '<option value="">— Select Winner —</option>';
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
            alert("Book at least one match first.");
            return;
        }

        // Validate winner override if manual
        for (const entry of card) {
            if (entry.winner_mode === "MANUAL" && !entry.winner_override_id) {
                e.preventDefault();
                alert(
                    "Please pick a winner for all matches set to Manual, " +
                    "or switch them back to Auto."
                );
                return;
            }
        }

        cardInput.value = JSON.stringify(card);
    });

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
            const winnerMode =
                slot.querySelector(".slot-winner-mode").value;
            const winnerOverrideId =
                slot.querySelector(".slot-winner-override").value || null;
            const storyId = slot.querySelector(".slot-story").value || null;

            // Auto-select championship type if a title is picked
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

                    // Find first empty slot
                    const emptySlot = Array.from(slotEls).find(
                        (s) =>
                            s.querySelectorAll(".drop-zone .wrestler-chip")
                                .length === 0
                    );
                    if (!emptySlot) {
                        alert("No empty match slots.");
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
                        chip.dataset.wrestlerName =
                            chipData.dataset.wrestlerName;
                        chip.dataset.gender = chipData.dataset.gender;
                        chip.textContent = chipData.dataset.wrestlerName;
                        zone.appendChild(chip);
                    });

                    // Set match type & importance
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
                    emptySlot.scrollIntoView({ behavior: "smooth", block: "center" });
                })
                .catch((err) => {
                    console.error(err);
                    alert("Could not fetch suggestion.");
                });
        });
    });

})();
