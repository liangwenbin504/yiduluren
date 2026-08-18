/* ================================================================
   仪度六壬择日 - 应用逻辑模块 (ynzr-app.js)
   依赖: ynzr-core.js, ynzr-daliuren.js
   包含: 择日主流程, 占事, 斗首, 演禽, 神煞, 日历, UI辅助, 全局包装器
   ================================================================ */

// ======================== 全局状态 ========================
let currentScoreData = null;
let currentSelectedDate = null;
let currentFourPillars = null;

// ======================== 数据常量 ========================
const solarTerms = {
    2026: [
        {name: '小寒', month: 1, day: 5}, {name: '大寒', month: 1, day: 20},
        {name: '立春', month: 2, day: 4}, {name: '雨水', month: 2, day: 19},
        {name: '惊蛰', month: 3, day: 5}, {name: '春分', month: 3, day: 20},
        {name: '清明', month: 4, day: 4}, {name: '谷雨', month: 4, day: 20},
        {name: '立夏', month: 5, day: 5}, {name: '小满', month: 5, day: 21},
        {name: '芒种', month: 6, day: 5}, {name: '夏至', month: 6, day: 21},
        {name: '小暑', month: 7, day: 7}, {name: '大暑', month: 7, day: 23},
        {name: '立秋', month: 8, day: 7}, {name: '处暑', month: 8, day: 23},
        {name: '白露', month: 9, day: 7}, {name: '秋分', month: 9, day: 23},
        {name: '寒露', month: 10, day: 8}, {name: '霜降', month: 10, day: 23},
        {name: '立冬', month: 11, day: 7}, {name: '小雪', month: 11, day: 22},
        {name: '大雪', month: 12, day: 7}, {name: '冬至', month: 12, day: 21}
    ],
    2027: [
        {name: '小寒', month: 1, day: 5}, {name: '大寒', month: 1, day: 20},
        {name: '立春', month: 2, day: 4}, {name: '雨水', month: 2, day: 18},
        {name: '惊蛰', month: 3, day: 5}, {name: '春分', month: 3, day: 20},
        {name: '清明', month: 4, day: 4}, {name: '谷雨', month: 4, day: 20},
        {name: '立夏', month: 5, day: 5}, {name: '小满', month: 5, day: 21},
        {name: '芒种', month: 6, day: 5}, {name: '夏至', month: 6, day: 21},
        {name: '小暑', month: 7, day: 7}, {name: '大暑', month: 7, day: 23},
        {name: '立秋', month: 8, day: 7}, {name: '处暑', month: 8, day: 23},
        {name: '白露', month: 9, day: 7}, {name: '秋分', month: 9, day: 23},
        {name: '寒露', month: 10, day: 8}, {name: '霜降', month: 10, day: 23},
        {name: '立冬', month: 11, day: 7}, {name: '小雪', month: 11, day: 22},
        {name: '大雪', month: 12, day: 7}, {name: '冬至', month: 12, day: 22}
    ],
    2028: [
        {name: '小寒', month: 1, day: 5}, {name: '大寒', month: 1, day: 20},
        {name: '立春', month: 2, day: 4}, {name: '雨水', month: 2, day: 18},
        {name: '惊蛰', month: 3, day: 5}, {name: '春分', month: 3, day: 20},
        {name: '清明', month: 4, day: 4}, {name: '谷雨', month: 4, day: 20},
        {name: '立夏', month: 5, day: 5}, {name: '小满', month: 5, day: 21},
        {name: '芒种', month: 6, day: 6}, {name: '夏至', month: 6, day: 21},
        {name: '小暑', month: 7, day: 7}, {name: '大暑', month: 7, day: 23},
        {name: '立秋', month: 8, day: 7}, {name: '处暑', month: 8, day: 23},
        {name: '白露', month: 9, day: 7}, {name: '秋分', month: 9, day: 23},
        {name: '寒露', month: 10, day: 8}, {name: '霜降', month: 10, day: 23},
        {name: '立冬', month: 11, day: 7}, {name: '小雪', month: 11, day: 22},
        {name: '大雪', month: 12, day: 7}, {name: '冬至', month: 12, day: 21}
    ],
    2029: [
        {name: '小寒', month: 1, day: 5}, {name: '大寒', month: 1, day: 20},
        {name: '立春', month: 2, day: 4}, {name: '雨水', month: 2, day: 18},
        {name: '惊蛰', month: 3, day: 5}, {name: '春分', month: 3, day: 20},
        {name: '清明', month: 4, day: 5}, {name: '谷雨', month: 4, day: 20},
        {name: '立夏', month: 5, day: 5}, {name: '小满', month: 5, day: 21},
        {name: '芒种', month: 6, day: 6}, {name: '夏至', month: 6, day: 21},
        {name: '小暑', month: 7, day: 7}, {name: '大暑', month: 7, day: 23},
        {name: '立秋', month: 8, day: 7}, {name: '处暑', month: 8, day: 23},
        {name: '白露', month: 9, day: 7}, {name: '秋分', month: 9, day: 23},
        {name: '寒露', month: 10, day: 8}, {name: '霜降', month: 10, day: 23},
        {name: '立冬', month: 11, day: 7}, {name: '小雪', month: 11, day: 22},
        {name: '大雪', month: 12, day: 7}, {name: '冬至', month: 12, day: 22}
    ],
    2030: [
        {name: '小寒', month: 1, day: 6}, {name: '大寒', month: 1, day: 20},
        {name: '立春', month: 2, day: 4}, {name: '雨水', month: 2, day: 19},
        {name: '惊蛰', month: 3, day: 5}, {name: '春分', month: 3, day: 21},
        {name: '清明', month: 4, day: 5}, {name: '谷雨', month: 4, day: 20},
        {name: '立夏', month: 5, day: 5}, {name: '小满', month: 5, day: 22},
        {name: '芒种', month: 6, day: 6}, {name: '夏至', month: 6, day: 21},
        {name: '小暑', month: 7, day: 7}, {name: '大暑', month: 7, day: 23},
        {name: '立秋', month: 8, day: 8}, {name: '处暑', month: 8, day: 23},
        {name: '白露', month: 9, day: 7}, {name: '秋分', month: 9, day: 23},
        {name: '寒露', month: 10, day: 8}, {name: '霜降', month: 10, day: 23},
        {name: '立冬', month: 11, day: 7}, {name: '小雪', month: 11, day: 22},
        {name: '大雪', month: 12, day: 7}, {name: '冬至', month: 12, day: 22}
    ]
};

const monthGanStart = {
    '甲': '丙', '乙': '戊', '丙': '庚', '丁': '壬', '戊': '甲',
    '己': '丙', '庚': '戊', '辛': '庚', '壬': '壬', '癸': '甲'
};

// ======================== 日历/四柱函数 ========================
function getTrueSolarTime(date, longitude = 120) {
    const lngDiff = (longitude - 120) * 4;
    const dayOfYear = Math.floor((date - new Date(date.getFullYear(), 0, 0)) / 86400000);
    const equationOfTime = 9.87 * Math.sin(2 * Math.PI * (dayOfYear - 81) / 365.25) - 
                            7.53 * Math.cos(Math.PI * (dayOfYear - 81) / 365.25) - 
                            1.5 * Math.sin(Math.PI * (dayOfYear - 81) / 365.25);
    const localTimeMinutes = date.getHours() * 60 + date.getMinutes();
    const trueSolarMinutes = localTimeMinutes + lngDiff + equationOfTime;
    const trueHour = ((Math.floor(trueSolarMinutes / 60) % 24) + 24) % 24;
    const trueMinute = Math.floor(Math.abs(trueSolarMinutes % 60));
    return { hour: trueHour, minute: trueMinute, longitude: longitude, offset: lngDiff + equationOfTime };
}

function initZhanshiTime() {
    const timeInput = document.getElementById('zhanshiTimeInput');
    const infoSpan = document.getElementById('trueSolarInfo');
    if (!timeInput) return;

    const defaultLng = 120;
    const now = new Date();

    function setTimeFromLng(lng, source) {
        const trueSolar = getTrueSolarTime(now, lng);
        const h = String(trueSolar.hour).padStart(2, '0');
        const m = String(trueSolar.minute).padStart(2, '0');
        timeInput.value = `${h}:${m}`;

        if (infoSpan) {
            const diff = trueSolar.offset;
            const sign = diff >= 0 ? '+' : '';
            const offsetMin = Math.round(diff);
            const lngLabel = source || `${lng}°E`;
            infoSpan.textContent = `☀️ 真太阳时 (${lngLabel}, 均时差${sign}${offsetMin}分)`;
            infoSpan.style.display = 'inline';
        }
    }

    function fallbackToGeo() {
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                function (pos) {
                    const lng = Math.round(pos.coords.longitude);
                    const label = `GPS ${lng}°E`;
                    setTimeFromLng(lng, label);
                },
                function () {
                    setTimeFromLng(defaultLng, '东八区');
                },
                { timeout: 3000, enableHighAccuracy: false }
            );
        } else {
            setTimeFromLng(defaultLng, '东八区');
        }
    }

    // 先设置默认值，避免等待API
    setTimeFromLng(defaultLng, '东八区');

    // 然后尝试获取精确位置
    fetch(API_BASE_URL + '/api/ip/location')
        .then(function (resp) { return resp.json(); })
        .then(function (data) {
            if (data.success && data.location) {
                var lng = Math.round(data.longitude);
                var label = data.location + ' (' + lng + '°E)';
                setTimeFromLng(lng, label);
            }
        })
        .catch(function (err) {
            console.log('IP定位API不可用，使用默认时区');
        });
}

function getYearGanZhi(year, month, day) {
    const yearTerms = solarTerms[year];
    if (!yearTerms) {
        const ganIndex = (year - 4) % 10;
        const zhiIndex = (year - 4) % 12;
        return [YNZR.data.tiangan[ganIndex], YNZR.data.dizhi[zhiIndex]];
    }
    const liChun = yearTerms.find(term => term.name === '立春');
    if (!liChun) {
        const ganIndex = (year - 4) % 10;
        const zhiIndex = (year - 4) % 12;
        return [YNZR.data.tiangan[ganIndex], YNZR.data.dizhi[zhiIndex]];
    }
    if (month > liChun.month || (month === liChun.month && day >= liChun.day)) {
        const ganIndex = (year - 4) % 10;
        const zhiIndex = (year - 4) % 12;
        return [YNZR.data.tiangan[ganIndex], YNZR.data.dizhi[zhiIndex]];
    } else {
        const prevYear = year - 1;
        const ganIndex = (prevYear - 4) % 10;
        const zhiIndex = (prevYear - 4) % 12;
        return [YNZR.data.tiangan[ganIndex], YNZR.data.dizhi[zhiIndex]];
    }
}

function getMonthGanZhi(year, month, day) {
    const yearTerms = solarTerms[year];
    if (!yearTerms) {
        const ganIndex = ((year - 4) % 10 * 2 + month) % 10;
        const zhiIndex = (month + 2) % 12;
        return [YNZR.data.tiangan[ganIndex], YNZR.data.dizhi[zhiIndex]];
    }
    const yearGanZhi = getYearGanZhi(year, month, day);
    const yearGan = yearGanZhi[0];
    let monthStart = 0;
    for (let i = 0; i < yearTerms.length; i += 2) {
        const zhongQi = yearTerms[i + 1];
        if (zhongQi) {
            if (i === 0) {
                if (month < zhongQi.month || (month === zhongQi.month && day < zhongQi.day)) {
                    const prevYearTerms = solarTerms[year - 1];
                    if (prevYearTerms) {
                        const prevZhongQi = prevYearTerms[prevYearTerms.length - 1];
                        if (month > prevZhongQi.month || (month === prevZhongQi.month && day >= prevZhongQi.day)) {
                            monthStart = 11;
                        }
                    }
                }
            } else {
                const prevZhongQi = yearTerms[i - 1];
                if ((month > prevZhongQi.month || (month === prevZhongQi.month && day >= prevZhongQi.day)) &&
                    (month < zhongQi.month || (month === zhongQi.month && day < zhongQi.day))) {
                    monthStart = Math.floor(i / 2);
                    break;
                }
            }
            if (i === yearTerms.length - 2) {
                const lastZhongQi = yearTerms[i + 1];
                if (month > lastZhongQi.month || (month === lastZhongQi.month && day >= lastZhongQi.day)) {
                    monthStart = Math.floor((i + 2) / 2) % 12;
                }
            }
        }
    }
    const startGan = monthGanStart[yearGan];
    const startGanIndex = YNZR.data.tiangan.indexOf(startGan);
    const monthGanIndex = (startGanIndex + monthStart) % 10;
    const monthZhiIndex = monthStart;
    return [YNZR.data.tiangan[monthGanIndex], YNZR.data.dizhi[monthZhiIndex]];
}

function getDayGanZhi(year, month, day) {
    const refYear = 4, refMonth = 1, refDay = 1;
    const targetDate = new Date(year, month - 1, day);
    const refDate = new Date(refYear, refMonth - 1, refDay);
    const diffDays = Math.floor((targetDate - refDate) / (1000 * 60 * 60 * 24));
    let leapAdjustment = 0;
    for (let y = refYear; y < year; y++) {
        if ((y % 4 === 0 && y % 100 !== 0) || (y % 400 === 0)) {
            leapAdjustment++;
        }
    }
    if (((year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0)) && month > 2) {
        leapAdjustment++;
    }
    const totalDays = diffDays + leapAdjustment;
    const ganIndex = totalDays % 10;
    const zhiIndex = totalDays % 12;
    return [YNZR.data.tiangan[ganIndex], YNZR.data.dizhi[zhiIndex]];
}

function getHourGanZhi(dayGan, hour, minute) {
    const date = new Date();
    date.setHours(hour, minute, 0, 0);
    const trueSolar = getTrueSolarTime(date);
    const trueHour = trueSolar.hour;
    let hourZhiIndex = Math.floor((trueHour + 1) / 2) % 12;
    const dayGanIndex = YNZR.data.tiangan.indexOf(dayGan);
    const hourGanStart = [0, 2, 4, 6, 8, 0, 2, 4, 6, 8][dayGanIndex % 5];
    const hourGanIndex = (hourGanStart + hourZhiIndex) % 10;
    return [YNZR.data.tiangan[hourGanIndex], YNZR.data.dizhi[hourZhiIndex]];
}

function getGanZhi(type, year, month, day, hour) {
    if (type === 'year') return getYearGanZhi(year, month, day);
    if (type === 'month') return getMonthGanZhi(year, month, day);
    if (type === 'day') return getDayGanZhi(year, month, day);
    const dayGanZhi = getDayGanZhi(year, month, day);
    return getHourGanZhi(dayGanZhi[0], hour, 0);
}

function getYueJiangByDate(year, month, day) {
    const yearTerms = solarTerms[year];
    if (!yearTerms) return '亥';
    let currentJieQi = null;
    for (let i = yearTerms.length - 1; i >= 0; i--) {
        const term = yearTerms[i];
        if (term.month < month || (term.month === month && term.day <= day)) {
            currentJieQi = term;
            break;
        }
    }
    if (!currentJieQi) {
        const prevYearTerms = solarTerms[year - 1];
        if (prevYearTerms) {
            for (let i = prevYearTerms.length - 1; i >= 0; i--) {
                const term = prevYearTerms[i];
                if (term.month < month || (term.month === month && term.day <= day)) {
                    currentJieQi = term;
                    break;
                }
            }
        }
    }
    if (!currentJieQi) return '亥';
    const jieQiToYueJiang = {
        '雨水': '亥', '春分': '戌', '谷雨': '酉', '小满': '申',
        '夏至': '未', '大暑': '午', '处暑': '巳', '秋分': '辰',
        '霜降': '卯', '小雪': '寅', '冬至': '丑', '大寒': '子'
    };
    for (const [jq, yj] of Object.entries(jieQiToYueJiang)) {
        const term = yearTerms.find(t => t.name === jq);
        if (term && (month > term.month || (month === term.month && day >= term.day))) {
            return yj;
        }
    }
    const firstTerm = yearTerms[0];
    if (month < firstTerm.month || (month === firstTerm.month && day < firstTerm.day)) {
        const prevYearTerms = solarTerms[year - 1];
        if (prevYearTerms) {
            for (const [jq, yj] of Object.entries(jieQiToYueJiang)) {
                const term = prevYearTerms.find(t => t.name === jq);
                if (term && (month > term.month || (month === term.month && day >= term.day))) {
                    return yj;
                }
            }
        }
    }
    return '亥';
}

function getShiChen(hour) {
    const shichenMap = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
    const index = Math.floor((hour + 1) / 2) % 12;
    return shichenMap[index];
}

// ======================== 神煞函数 ========================
const GUIREN_SONG = {
    '甲': ['丑', '未'], '戊': ['丑', '未'], '庚': ['丑', '未'],
    '乙': ['子', '申'], '己': ['子', '申'],
    '丙': ['亥', '酉'], '丁': ['亥', '酉'],
    '壬': ['卯', '巳'], '癸': ['卯', '巳'],
    '辛': ['寅', '午']
};

function calculateGuiRenZhi(dayGan, hourZhi) {
    const guiRenList = GUIREN_SONG[dayGan];
    if (!guiRenList) return null;
    const DIZHI_ORDER = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
    const hourIndex = DIZHI_ORDER.indexOf(hourZhi);
    if (hourIndex === -1) return null;
    const yangHour = DIZHI_ORDER.indexOf(guiRenList[0]);
    const yinHour = DIZHI_ORDER.indexOf(guiRenList[1]);
    const dayIndex = DIZHI_ORDER.indexOf(dayGan);
    if (hourIndex >= 4 && hourIndex <= 9) {
        return DIZHI_ORDER[yangHour];
    } else {
        return DIZHI_ORDER[yinHour];
    }
}

function calculateGuiRen(dayGan, hourZhi) {
    const guiRenList = GUIREN_SONG[dayGan];
    if (!guiRenList) return { guiRen: '--', isShun: true, guiRenName: '--' };
    const DIZHI_ORDER = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
    const hourIndex = DIZHI_ORDER.indexOf(hourZhi);
    if (hourIndex === -1) return { guiRen: '--', isShun: true, guiRenName: '--' };
    const isDayTime = hourIndex >= 4 && hourIndex <= 9;
    const guiRenZhi = isDayTime ? guiRenList[0] : guiRenList[1];
    const guiRenMap = { '丑': '贵人', '子': '贵人', '亥': '贵人', '酉': '贵人', '巳': '贵人', '午': '贵人', '寅': '贵人', '申': '贵人', '卯': '贵人', '未': '贵人' };
    return { guiRen: guiRenZhi, isShun: isDayTime, guiRenName: guiRenMap[guiRenZhi] || '贵人' };
}

function calculateXunKongArray(dayGan, dayZhi) {
    const ganIndex = YNZR.data.tiangan.indexOf(dayGan);
    const zhiIndex = YNZR.data.dizhi.indexOf(dayZhi);
    if (ganIndex === -1 || zhiIndex === -1) return [];
    const xunStart = Math.floor(ganIndex / 10) * 10;
    const xunZhiStart = ganIndex - xunStart;
    const xunEndZhi = (xunZhiStart + 9) % 12;
    if (zhiIndex > xunEndZhi) return [];
    const emptyIndex1 = (xunEndZhi + 1) % 12;
    const emptyIndex2 = (xunEndZhi + 2) % 12;
    return [YNZR.data.dizhi[emptyIndex1], YNZR.data.dizhi[emptyIndex2]];
}

function calculateXunKong(dayGan, dayZhi) {
    const arr = calculateXunKongArray(dayGan, dayZhi);
    return arr.join('、');
}

function calculateYiMa(dayZhi) {
    const yiMaMap = {
        '寅': '申', '午': '申', '戌': '申',
        '巳': '亥', '酉': '亥', '丑': '亥',
        '申': '寅', '子': '寅', '辰': '寅',
        '亥': '巳', '卯': '巳', '未': '巳'
    };
    return yiMaMap[dayZhi] || '';
}

function calculateLiuQin(riGan, zhi) {
    const wuxingMap = { '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水' };
    const zhiWuxingMap = {
        '寅': '木', '卯': '木', '巳': '火', '午': '火',
        '辰': '土', '戌': '土', '丑': '土', '未': '土',
        '申': '金', '酉': '金', '亥': '水', '子': '水'
    };
    const liuqinMap = { '金': '官鬼', '木': '兄弟', '水': '父母', '火': '妻财', '土': '子孙' };
    const riWuxing = wuxingMap[riGan];
    const zhiWuxing = zhiWuxingMap[zhi];
    if (!riWuxing || !zhiWuxing) return '--';
    const keMap = { '木': ['土'], '土': ['水'], '水': ['火'], '火': ['金'], '金': ['木'] };
    if (riWuxing === zhiWuxing) return '兄弟';
    if (keMap[riWuxing] && keMap[riWuxing].includes(zhiWuxing)) return '妻财';
    if (keMap[zhiWuxing] && keMap[zhiWuxing].includes(riWuxing)) return '官鬼';
    const shengMap = { '木': '火', '火': '土', '土': '金', '金': '水', '水': '木' };
    if (shengMap[riWuxing] === zhiWuxing) return '子孙';
    if (shengMap[zhiWuxing] === riWuxing) return '父母';
    return '兄弟';
}

/**
 * 计算全部神煞（年煞、月煞、日煞）
 * @param {string} dayGan - 日干
 * @param {string} dayZhi - 日支
 * @param {string} yearZhi - 年支
 * @param {string} monthZhi - 月支（月建）
 * @returns {Object} { nianSha: {}, yueSha: {}, riSha: {} }
 */
function calculateAllShenSha(dayGan, dayZhi, yearZhi, monthZhi) {
    const DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];

    // ========== 年支神煞 ==========
    const nianSha = {};

    // 丧门吊客
    const SANG_DIAO = {
        '子': ['寅', '戌'], '丑': ['卯', '亥'], '寅': ['辰', '子'],
        '卯': ['巳', '丑'], '辰': ['午', '寅'], '巳': ['未', '卯'],
        '午': ['申', '辰'], '未': ['酉', '巳'], '申': ['戌', '午'],
        '酉': ['亥', '未'], '戌': ['子', '申'], '亥': ['丑', '酉']
    };
    if (SANG_DIAO[yearZhi]) {
        nianSha['丧门'] = SANG_DIAO[yearZhi][0];
        nianSha['吊客'] = SANG_DIAO[yearZhi][1];
    }

    // 孤辰寡宿
    const GU_GUA = {
        '亥': {孤: '寅',寡: '戌'}, '子': {孤: '寅',寡: '戌'}, '丑': {孤: '寅',寡: '戌'},
        '寅': {孤: '巳',寡: '丑'}, '卯': {孤: '巳',寡: '丑'}, '辰': {孤: '巳',寡: '丑'},
        '巳': {孤: '申',寡: '辰'}, '午': {孤: '申',寡: '辰'}, '未': {孤: '申',寡: '辰'},
        '申': {孤: '亥',寡: '未'}, '酉': {孤: '亥',寡: '未'}, '戌': {孤: '亥',寡: '未'}
    };
    if (GU_GUA[yearZhi]) {
        nianSha['孤辰'] = GU_GUA[yearZhi].孤;
        nianSha['寡宿'] = GU_GUA[yearZhi].寡;
    }

    // 病符 = 年支前一位
    const bingFuIndex = (DIZHI.indexOf(yearZhi) - 1 + 12) % 12;
    nianSha['病符'] = DIZHI[bingFuIndex];

    // 岁破 = 年支对冲
    const LIU_CHONG = {
        '子': '午', '丑': '未', '寅': '申', '卯': '酉',
        '辰': '戌', '巳': '亥', '午': '子', '未': '丑',
        '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'
    };
    nianSha['岁破'] = LIU_CHONG[yearZhi] || '';

    // ========== 月建神煞 ==========
    const yueSha = {};

    // 月建 = monthZhi
    yueSha['月建'] = monthZhi;

    // 月破 = 月建对冲
    yueSha['月破'] = LIU_CHONG[monthZhi] || '';

    // 月煞表（按monthZhi索引）
    const YUE_SHA_TABLE = {
        '寅': {月厌: '戌', 天德: '丁', 月德: '丁', 天喜: '戌', 天医: '辰'},
        '卯': {月厌: '酉', 天德: '坤', 月德: '申', 天喜: '亥', 天医: '巳'},
        '辰': {月厌: '申', 天德: '壬', 月德: '壬', 天喜: '子', 天医: '午'},
        '巳': {月厌: '未', 天德: '辛', 月德: '辛', 天喜: '丑', 天医: '未'},
        '午': {月厌: '午', 天德: '乾', 月德: '亥', 天喜: '寅', 天医: '申'},
        '未': {月厌: '巳', 天德: '甲', 月德: '甲', 天喜: '卯', 天医: '酉'},
        '申': {月厌: '辰', 天德: '癸', 月德: '癸', 天喜: '辰', 天医: '戌'},
        '酉': {月厌: '卯', 天德: '艮', 月德: '寅', 天喜: '巳', 天医: '亥'},
        '戌': {月厌: '寅', 天德: '丙', 月德: '丙', 天喜: '午', 天医: '子'},
        '亥': {月厌: '丑', 天德: '乙', 月德: '乙', 天喜: '未', 天医: '丑'},
        '子': {月厌: '子', 天德: '巽', 月德: '巳', 天喜: '申', 天医: '寅'},
        '丑': {月厌: '亥', 天德: '庚', 月德: '庚', 天喜: '酉', 天医: '卯'}
    };
    const yueShaData = YUE_SHA_TABLE[monthZhi];
    if (yueShaData) {
        yueSha['月厌'] = yueShaData.月厌;
        yueSha['天德'] = yueShaData.天德;
        yueSha['月德'] = yueShaData.月德;
        yueSha['天喜'] = yueShaData.天喜;
        yueSha['天医'] = yueShaData.天医;
    }

    // 天赦（按季节）
    const TIAN_SHE = {
        '寅': '戊寅', '卯': '戊寅', '辰': '戊寅',
        '巳': '甲午', '午': '甲午', '未': '甲午',
        '申': '戊申', '酉': '戊申', '戌': '戊申',
        '亥': '甲子', '子': '甲子', '丑': '甲子'
    };
    if (TIAN_SHE[monthZhi]) yueSha['天赦'] = TIAN_SHE[monthZhi];

    // 四废（按季节）
    const SI_FEI = {
        '寅': '庚申辛酉', '卯': '庚申辛酉', '辰': '庚申辛酉',
        '巳': '壬子癸亥', '午': '壬子癸亥', '未': '壬子癸亥',
        '申': '甲寅乙卯', '酉': '甲寅乙卯', '戌': '甲寅乙卯',
        '亥': '丙午丁巳', '子': '丙午丁巳', '丑': '丙午丁巳'
    };
    if (SI_FEI[monthZhi]) yueSha['四废'] = SI_FEI[monthZhi];

    // ========== 日干神煞 ==========
    const riSha = {};

    // 日禄
    const RI_LU = { '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳', '己': '午', '庚': '申', '辛': '酉', '壬': '亥', '癸': '子' };
    riSha['日禄'] = RI_LU[dayGan] || '';

    // 羊刃
    const YANG_REN = { '甲': '卯', '乙': '寅', '丙': '午', '丁': '巳', '戊': '午', '己': '巳', '庚': '酉', '辛': '申', '壬': '子', '癸': '亥' };
    riSha['羊刃'] = YANG_REN[dayGan] || '';

    // 天乙贵人
    const GUI_REN = {
        '甲': ['丑', '未'], '戊': ['丑', '未'], '庚': ['丑', '未'],
        '乙': ['子', '申'], '己': ['子', '申'],
        '丙': ['亥', '酉'], '丁': ['亥', '酉'],
        '壬': ['巳', '卯'], '癸': ['巳', '卯'],
        '辛': ['午', '寅']
    };
    if (GUI_REN[dayGan]) {
        riSha['天乙贵人'] = GUI_REN[dayGan].join('、');
    }

    // 驿马（按日支三合）
    const YI_MA = { '申': '寅', '子': '寅', '辰': '寅', '亥': '巳', '卯': '巳', '未': '巳', '寅': '申', '午': '申', '戌': '申', '巳': '亥', '酉': '亥', '丑': '亥' };
    riSha['驿马'] = YI_MA[dayZhi] || '';

    // 桃花（按日支三合）
    const TAO_HUA = { '申': '酉', '子': '酉', '辰': '酉', '亥': '子', '卯': '子', '未': '子', '寅': '卯', '午': '卯', '戌': '卯', '巳': '午', '酉': '午', '丑': '午' };
    riSha['桃花'] = TAO_HUA[dayZhi] || '';

    // 劫煞（按日支三合）
    const JIE_SHA = { '申': '巳', '子': '巳', '辰': '巳', '亥': '申', '卯': '申', '未': '申', '寅': '亥', '午': '亥', '戌': '亥', '巳': '寅', '酉': '寅', '丑': '寅' };
    riSha['劫煞'] = JIE_SHA[dayZhi] || '';

    // 灾煞（按日支三合）
    const ZAI_SHA = { '申': '午', '子': '午', '辰': '午', '亥': '酉', '卯': '酉', '未': '酉', '寅': '子', '午': '子', '戌': '子', '巳': '卯', '酉': '卯', '丑': '卯' };
    riSha['灾煞'] = ZAI_SHA[dayZhi] || '';

    // 日破 = 日支对冲
    riSha['日破'] = LIU_CHONG[dayZhi] || '';

    // 旬空
    const xunKong = calculateXunKong(dayGan, dayZhi);
    if (xunKong) riSha['旬空'] = xunKong;

    // 天罗地网（戌亥日天罗在辰，辰巳日地网在戌）
    if (dayZhi === '戌' || dayZhi === '亥') {
        riSha['天罗'] = '辰';
    }
    if (dayZhi === '辰' || dayZhi === '巳') {
        riSha['地网'] = '戌';
    }

    return { nianSha, yueSha, riSha };
}

// ======================== 贵人盘显示 ========================
function updateGuiRenDisplay(result) {
    const tianJiang = result.tianJiangMap;
    const tianPan = result.tianPan;
    const tianPanPosition = {};
    let tianPanArray = [];
    if (typeof tianPan === 'object' && !Array.isArray(tianPan)) {
        const DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
        tianPanArray = DIZHI.map(zhi => tianPan[zhi] || '');
    } else if (Array.isArray(tianPan)) {
        tianPanArray = tianPan;
    } else {
        console.error('天盘数据格式错误:', tianPan);
        return;
    }
    if (tianPanArray[5]) tianPanPosition[tianPanArray[5]] = { row: 2, col: 2 };
    if (tianPanArray[6]) tianPanPosition[tianPanArray[6]] = { row: 2, col: 3 };
    if (tianPanArray[7]) tianPanPosition[tianPanArray[7]] = { row: 2, col: 4 };
    if (tianPanArray[8]) tianPanPosition[tianPanArray[8]] = { row: 2, col: 5 };
    if (tianPanArray[4]) tianPanPosition[tianPanArray[4]] = { row: 3, col: 2 };
    if (tianPanArray[9]) tianPanPosition[tianPanArray[9]] = { row: 3, col: 5 };
    if (tianPanArray[3]) tianPanPosition[tianPanArray[3]] = { row: 4, col: 2 };
    if (tianPanArray[10]) tianPanPosition[tianPanArray[10]] = { row: 4, col: 5 };
    if (tianPanArray[2]) tianPanPosition[tianPanArray[2]] = { row: 5, col: 2 };
    if (tianPanArray[1]) tianPanPosition[tianPanArray[1]] = { row: 5, col: 3 };
    if (tianPanArray[0]) tianPanPosition[tianPanArray[0]] = { row: 5, col: 4 };
    if (tianPanArray[11]) tianPanPosition[tianPanArray[11]] = { row: 5, col: 5 };

    const guirenPosition = {};
    for (const zhiName in tianPanPosition) {
        const pos = tianPanPosition[zhiName];
        if (pos.row === 2) {
            guirenPosition[zhiName] = { row: 1, col: pos.col };
        } else if (pos.row === 5) {
            guirenPosition[zhiName] = { row: 6, col: pos.col };
        } else if (pos.col === 2) {
            guirenPosition[zhiName] = { row: pos.row, col: 1 };
        } else if (pos.col === 5) {
            guirenPosition[zhiName] = { row: pos.row, col: 6 };
        }
    }

    const guirenCells = document.querySelectorAll('.guiren-outer-cell');
    guirenCells.forEach(cell => cell.remove());

    for (let i = 0; i < 12; i++) {
        const tianPanZhi = tianPanArray[i];
        if (!tianPanZhi) continue;

        let tianJiangName = '--';
        if (typeof tianJiang === 'object' && !Array.isArray(tianJiang)) {
            tianJiangName = tianJiang[tianPanZhi] || '--';
        } else if (Array.isArray(tianJiang)) {
            const tjMap = {};
            for (let j = 0; j < 12; j++) {
                if (tianJiang[j]) {
                    const tpZhi = tianPanArray[j];
                    tjMap[tpZhi] = tianJiang[j]?.tianJiang || tianJiang[j];
                }
            }
            tianJiangName = tjMap[tianPanZhi] || '--';
        }
        if (tianJiangName === '--') continue;

        const position = guirenPosition[tianPanZhi];
        if (!position) continue;

        const cell = document.createElement('div');
        cell.className = 'guiren-outer-cell';
        cell.style.gridColumn = position.col;
        cell.style.gridRow = position.row;
        cell.dataset.index = i;

        const valueEl = document.createElement('div');
        valueEl.className = 'guiren-outer-value';
        valueEl.textContent = tianJiangName;
        cell.appendChild(valueEl);

        const guirenOuterWrapper = document.querySelector('.guiren-outer-wrapper');
        if (guirenOuterWrapper) {
            guirenOuterWrapper.appendChild(cell);
        }
    }
}

// ======================== 大六壬Wrapper ========================
async function daliurenPaiPan(year, month, day, hour, dayGan, dayZhi) {
    if (dayGan && dayZhi) {
        const result = await daLiuRenPaiPan(year, month, day, hour, null, dayGan, dayZhi);
        if (result) {
            updateTianDiPanDisplay(result);
            updateGuiRenDisplay(result);
            updateSiKeDisplay(result);
            updateSanChuanDisplay(result);
            updateYuejiangDisplay(result);
            const shenshaYimaEl = document.getElementById('shenshaYima');
            if (shenshaYimaEl) {
                const yima = calculateYiMa(result.riZhi);
                shenshaYimaEl.textContent = yima || '--';
            }
            const shenshaXunkongEl = document.getElementById('shenshaXunkong');
            if (shenshaXunkongEl) {
                const xunkong = calculateXunKong(result.riGan, result.riZhi);
                shenshaXunkongEl.textContent = xunkong || '--';
            }
            const daliurenShijianEl = document.getElementById('daliurenShijian');
            if (daliurenShijianEl) {
                const shiChen = result.shiChen || getShiChen(hour);
                const yueJiangName = result.yueJiangName || (YNZR.data.yueJiangNames[result.yueJiang] || result.yueJiang);
                daliurenShijianEl.textContent = `${year}年${month}月${day}日 ${shiChen}时 月将${result.yueJiang}(${yueJiangName})`;
            }
            const ketiInfoEl = document.getElementById('ketiInfo');
            if (ketiInfoEl && result.keTi) {
                ketiInfoEl.textContent = result.keTi;
            }
        }
        return result;
    }
    return null;
}

// ======================== 择日主流程 ========================
async function calculateDate(dateStr, hourName = null, scoreData = null) {
    if (!dateStr) {
        console.error('无效的日期字符串');
        return;
    }
    currentScoreData = scoreData;
    const currentMountain = YNZR.getCurrentMountain();
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
        console.error('无效的日期格式');
        return;
    }
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    currentSelectedDate = { dateStr, year, month, day, hourName };

    let hour = date.getHours();
    if (hourName) {
        const shichenMap = { '子': 0, '丑': 2, '寅': 4, '卯': 6, '辰': 8, '巳': 10, '午': 12, '未': 14, '申': 16, '酉': 18, '戌': 20, '亥': 22 };
        const dizhi = hourName.replace('时', '');
        if (shichenMap[dizhi] !== undefined) hour = shichenMap[dizhi];
    }

    let fourPillars;
    try {
        const shichen = getShiChen(hour);
        const sizhuResponse = await fetch(`${API_BASE_URL}/api/sizhu?year=${year}&month=${month}&day=${day}&hour=${hour}`);
        if (sizhuResponse.ok) {
            const sizhuResult = await sizhuResponse.json();
            if (sizhuResult.success && sizhuResult.sizhu) {
                const sz = sizhuResult.sizhu;
                fourPillars = {
                    year: sz.yearPillar, month: sz.monthPillar, day: sz.dayPillar, hour: sz.hourPillar,
                    details: { yearGan: sz.yearGan, yearZhi: sz.yearZhi, monthGan: sz.monthGan, monthZhi: sz.monthZhi, dayGan: sz.dayGan, dayZhi: sz.dayZhi, hourGan: sz.hourGan, hourZhi: sz.hourZhi }
                };
                currentFourPillars = fourPillars;
            } else {
                throw new Error(sizhuResult.error || '四柱计算失败');
            }
        } else {
            throw new Error('四柱API请求失败');
        }

        const yearPillarEl = document.getElementById('yearPillar');
        const monthPillarEl = document.getElementById('monthPillar');
        const dayPillarEl = document.getElementById('dayPillar');
        const hourPillarEl = document.getElementById('hourPillar');
        if (yearPillarEl) yearPillarEl.textContent = fourPillars.year;
        if (monthPillarEl) monthPillarEl.textContent = fourPillars.month;
        if (dayPillarEl) dayPillarEl.textContent = fourPillars.day;
        if (hourPillarEl) hourPillarEl.textContent = fourPillars.hour;

        const zuoshanSelectDisplay = document.getElementById('zuoshanSelectDisplay');
        const mountainWuxing = zuoshanSelectDisplay?.dataset?.mountainElement || null;
        updateDoushouDisplay(mountainWuxing);
        await updateYanqinDisplay(year, month, day);
    } catch (error) {
        console.error('四柱计算失败:', error);
        alert('四柱计算出错，请检查日期设置');
        return;
    }

    let paipanResult = null;
    try {
        const dayGanZhi = fourPillars?.day;
        if (dayGanZhi) {
            const dayGan = dayGanZhi.charAt(0);
            const dayZhi = dayGanZhi.charAt(1);
            let sixPhaseWarning = null;
            if (currentMountain && window.judgeSixPhaseLuck) {
                try {
                    const sixPhaseResult = window.judgeSixPhaseLuck(currentMountain, dayGan, dayZhi);
                    if (sixPhaseResult.luck === '大凶') sixPhaseWarning = sixPhaseResult;
                } catch (e) { console.error('六相六替检查失败:', e); }
            }
            paipanResult = await daliurenPaiPan(year, month, day, hour, dayGan, dayZhi);
        }
    } catch (error) {
        console.error('大六壬排盘失败:', error);
    }

    let doushouResult = null;
    if (currentScoreData && currentScoreData.doushouScore) {
        doushouResult = { score: currentScoreData.doushouScore, keti: currentScoreData.doushouJixiong || '--', details: {} };
        const doushouScoreEl = document.getElementById('doushouScore');
        const doushouKetiEl = document.getElementById('doushouKeti');
        if (doushouScoreEl) doushouScoreEl.textContent = doushouResult.score;
        if (doushouKetiEl) doushouKetiEl.textContent = doushouResult.keti;
    } else if (currentMountain && fourPillars) {
        try {
            const doushouResponse = await fetch(`${API_BASE_URL}/api/doushou/full_analyze`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mountain: currentMountain, sizhu: { '年柱': fourPillars.year, '月柱': fourPillars.month, '日柱': fourPillars.day, '时柱': fourPillars.hour } })
            });
            if (doushouResponse.ok) {
                const doushouData = await doushouResponse.json();
                if (doushouData.success && doushouData.result) {
                    doushouResult = { score: doushouData.result['综合评分'] || 0, keti: doushouData.result['吉凶等级'] || '--', patterns: doushouData.result['课格格局'] || [], duanyu: doushouData.result['吉凶断语'] || [], details: doushouData.result };
                    const doushouScoreEl = document.getElementById('doushouScore');
                    const doushouKetiEl = document.getElementById('doushouKeti');
                    if (doushouScoreEl) doushouScoreEl.textContent = doushouResult.score;
                    if (doushouKetiEl) doushouKetiEl.textContent = doushouResult.keti;
                }
            }
        } catch (error) { console.error('斗首择日计算失败:', error); }
    } else {
        const doushouScoreEl = document.getElementById('doushouScore');
        const doushouKetiEl = document.getElementById('doushouKeti');
        if (doushouScoreEl) doushouScoreEl.textContent = '--';
        if (doushouKetiEl) doushouKetiEl.textContent = '--';
    }

    const daliurenScoreEl = document.getElementById('daliurenScore');
    const daliurenKetiEl = document.getElementById('daliurenKeti');
    if (currentScoreData && currentScoreData.daliurenScore) {
        if (daliurenScoreEl) daliurenScoreEl.textContent = currentScoreData.daliurenScore;
        if (daliurenKetiEl) daliurenKetiEl.textContent = currentScoreData.daliurenKeti || paipanResult?.keTi || '--';
    } else if (paipanResult && paipanResult.keTi) {
        let score = 70;
        if (paipanResult.keTi.includes('元首') || paipanResult.keTi.includes('龙德') || paipanResult.keTi.includes('富贵')) score = 90;
        else if (paipanResult.keTi.includes('重审') || paipanResult.keTi.includes('知一')) score = 75;
        else if (paipanResult.keTi.includes('涉害') || paipanResult.keTi.includes('遥克')) score = 65;
        else if (paipanResult.keTi.includes('昴星') || paipanResult.keTi.includes('别责')) score = 55;
        else if (paipanResult.keTi.includes('八专') || paipanResult.keTi.includes('伏吟') || paipanResult.keTi.includes('反吟')) score = 45;
        if (daliurenScoreEl) daliurenScoreEl.textContent = score;
        if (daliurenKetiEl) daliurenKetiEl.textContent = paipanResult.keTi;
    } else {
        if (daliurenScoreEl) daliurenScoreEl.textContent = '--';
        if (daliurenKetiEl) daliurenKetiEl.textContent = '--';
    }

    updateAIEvaluation();

    const zuoshan = currentMountain || '壬';
    const riGan = fourPillars ? fourPillars.day.charAt(0) : '甲';
    const douShouResult = doushouResult || {};
    const dateInfo = { shan: zuoshan, riGan, douShou: douShouResult.doushouElement || '元辰', score: douShouResult.score || 0, keti: douShouResult.keti || '元辰旺相', doushouResult: douShouResult };
}

async function updateAIEvaluation() {
    const aiEvaluationTitle = document.querySelector('.ai-evaluation-title');
    if (aiEvaluationTitle) aiEvaluationTitle.textContent = '综合评价';

    const sizhuTitle = document.querySelector('.sizhu-panel .panel-title');
    if (sizhuTitle && currentSelectedDate) {
        const { year, month, day, hourName } = currentSelectedDate;
        sizhuTitle.textContent = `四柱（${year}年${month}月${day}日${hourName || ''}）`;
    } else if (sizhuTitle) {
        sizhuTitle.textContent = '四柱';
    }

    let doushouScore, doushouKeti, daliurenScore, daliurenKeti, yanqinScore, yanqinInfo;
    let doushouJixiong, daliurenJixiong, yanqinJixiong;

    if (currentScoreData) {
        doushouScore = currentScoreData.doushouScore || 0;
        doushouKeti = currentScoreData.doushouKeti || '--';
        doushouJixiong = currentScoreData.doushouJixiong || '平';
        daliurenScore = currentScoreData.daliurenScore || 0;
        daliurenKeti = currentScoreData.daliurenKeti || '--';
        daliurenJixiong = currentScoreData.daliurenJixiong || '平';
        yanqinScore = currentScoreData.yanqinScore || 0;
        yanqinInfo = currentScoreData.yanqinInfo || '--';
        yanqinJixiong = currentScoreData.yanqinJixiong || '平';
    } else {
        const doushouScoreEl = document.getElementById('doushouScore');
        const doushouKetiEl = document.getElementById('doushouKeti');
        const doushouScoreText = doushouScoreEl ? doushouScoreEl.textContent : '--';
        doushouScore = doushouScoreText && doushouScoreText !== '--' ? parseInt(doushouScoreText) : 0;
        doushouKeti = doushouKetiEl ? doushouKetiEl.textContent : '--';
        doushouJixiong = doushouScore >= 70 ? '吉' : (doushouScore >= 50 ? '平' : '凶');

        const daliurenScoreEl = document.getElementById('daliurenScore');
        const daliurenKetiEl = document.getElementById('daliurenKeti');
        const daliurenScoreText = daliurenScoreEl ? daliurenScoreEl.textContent : '--';
        daliurenScore = daliurenScoreText && daliurenScoreText !== '--' ? parseInt(daliurenScoreText) : 0;
        daliurenKeti = daliurenKetiEl ? daliurenKetiEl.textContent : '--';
        daliurenJixiong = daliurenScore >= 70 ? '吉' : (daliurenScore >= 50 ? '平' : '凶');

        const dayYanqinEl = document.getElementById('dayYanqin');
        yanqinScore = 0;
        yanqinInfo = '';
        if (dayYanqinEl) {
            const yanqinText = dayYanqinEl.textContent.trim();
            if (yanqinText && yanqinText !== '--') {
                yanqinInfo = yanqinText;
                yanqinScore = yanqinText.includes('吉') ? 90 : (yanqinText.includes('平') ? 70 : 30);
            }
        }
        yanqinJixiong = yanqinScore >= 85 ? '吉' : (yanqinScore >= 70 ? '平' : '凶');
    }

    const lailongSelect = document.getElementById('lailongSelect');
    const lailong = lailongSelect ? lailongSelect.value : '';
    let liunianResult = null;
    if (lailong) {
        const startYear = document.getElementById('startYear').value;
        if (startYear) {
            const mountain = lailong.replace('龙', '');
            liunianResult = calculateLongLuck(mountain, parseInt(startYear));
        }
    }

    let traditionalDuanyu = '';
    try {
        let ketiList = [];
        if (currentScoreData?.patterns && currentScoreData.patterns.length > 0) {
            const doushouPatterns = currentScoreData.patterns.map(p => {
                if (typeof p === 'string') return p;
                if (p && p['格局名称']) return p['格局名称'];
                return null;
            }).filter(k => k);
            ketiList = ketiList.concat(doushouPatterns);
        }
        const daliurenKetiValue = currentScoreData?.daliurenKeti || daliurenKeti;
        if (daliurenKetiValue && daliurenKetiValue !== '--') {
            // 课体可能已拼接课格（如 "重审课 · 玄胎"），拆分后逐个加入，避免把整串当成一个课格
            for (const k of daliurenKetiValue.split(' · ')) {
                const kk = k.trim();
                if (kk && !ketiList.includes(kk)) ketiList.push(kk);
            }
        }
        if (ketiList.length === 0) {
            const daliurenKetiEl = document.getElementById('daliurenKeti');
            if (daliurenKetiEl && daliurenKetiEl.textContent && daliurenKetiEl.textContent !== '--') {
                ketiList.push(daliurenKetiEl.textContent);
            }
        }

        if (ketiList.length > 0) {
            let mountainValue = '';
            const zuoshanDisplay = document.getElementById('zuoshanSelectDisplay');
            if (zuoshanDisplay) mountainValue = zuoshanDisplay.dataset.value || '';

            const selectedMubiao = getSelectedMubiao();
            const requestData = {
                '课格列表': ketiList, 'mountain': mountainValue, '坐山': mountainValue,
                'mubiao': selectedMubiao, '求课目标': selectedMubiao,
                'luma_guiren_info': currentScoreData?.luma_guiren_info || null,
                'sizhu': {
                    '年柱': document.getElementById('yearPillar')?.textContent || '',
                    '月柱': document.getElementById('monthPillar')?.textContent || '',
                    '日柱': document.getElementById('dayPillar')?.textContent || '',
                    '时柱': document.getElementById('hourPillar')?.textContent || ''
                },
                '三传': {
                    '初传': { '六亲': document.getElementById('chuanchuLiuqin')?.textContent || '', '日干': document.getElementById('chuanchuRigan')?.textContent || '', '地支': document.getElementById('chuanchuDizhi')?.textContent || '', '贵人': document.getElementById('chuanchuGuiren')?.textContent || '' },
                    '中传': { '六亲': document.getElementById('zhongchuanLiuqin')?.textContent || '', '日干': document.getElementById('zhongchuanRigan')?.textContent || '', '地支': document.getElementById('zhongchuanDizhi')?.textContent || '', '贵人': document.getElementById('zhongchuanGuiren')?.textContent || '' },
                    '末传': { '六亲': document.getElementById('mochuanLiuqin')?.textContent || '', '日干': document.getElementById('mochuanRigan')?.textContent || '', '地支': document.getElementById('mochuanDizhi')?.textContent || '', '贵人': document.getElementById('mochuanGuiren')?.textContent || '' }
                },
                '斗首课格': doushouKeti, '斗首评分': doushouScore, '六壬评分': daliurenScore,
                'yanqinScore': yanqinScore, 'yanqin': yanqinInfo, 'yanqinInfo': yanqinInfo
            };

            const result = await fetchApi(`${API_BASE_URL}/ai/traditional_duanyu`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            if (result && result.success && result.traditional_duanyu) {
                traditionalDuanyu = result.traditional_duanyu;
            }
        }
    } catch (error) {
        console.error('获取传统断语失败:', error);
    }

    let evaluation = '';
    if (traditionalDuanyu) {
        evaluation = traditionalDuanyu;
    } else {
        evaluation = '【提示】暂无断语库内容，请检查课格信息是否正确传递。';
    }
    document.getElementById('aiEvaluation').textContent = evaluation;
}

// ======================== 斗首函数 ========================
function calculateDoushouWuxing(mountainElement, tiangan) {
    const wuxingMap = {
        '甲': '木', '乙': '木', '丙': '火', '丁': '火',
        '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'
    };
    const keMap = { '木': '土', '土': '水', '水': '火', '火': '金', '金': '木' };
    const shengMap = { '木': '火', '火': '土', '土': '金', '金': '水', '水': '木' };
    const ganWuxing = wuxingMap[tiangan];
    if (!ganWuxing || !mountainElement) return { wuxing: ganWuxing, doushou: '元辰', color: '#333333' };
    const doushouNames = {
        'same': { name: '元辰', color: '#8B4513' },
        'keWo': { name: '廉贞', color: '#FF0000' },
        'woKe': { name: '武财', color: '#FFD700' },
        'shengWo': { name: '贪狼', color: '#008000' },
        'woSheng': { name: '巨门', color: '#0000FF' }
    };
    if (mountainElement === ganWuxing) return { wuxing: ganWuxing, ...doushouNames.same };
    if (keMap[mountainElement] === ganWuxing) return { wuxing: ganWuxing, ...doushouNames.keWo };
    if (keMap[ganWuxing] === mountainElement) return { wuxing: ganWuxing, ...doushouNames.woKe };
    if (shengMap[mountainElement] === ganWuxing) return { wuxing: ganWuxing, ...doushouNames.shengWo };
    if (shengMap[ganWuxing] === mountainElement) return { wuxing: ganWuxing, ...doushouNames.woSheng };
    return { wuxing: ganWuxing, ...doushouNames.same };
}

function updateDoushouDisplay(mountainWuxing) {
    const yearPillarEl = document.getElementById('yearPillar');
    const monthPillarEl = document.getElementById('monthPillar');
    const dayPillarEl = document.getElementById('dayPillar');
    const hourPillarEl = document.getElementById('hourPillar');
    if (!yearPillarEl || !monthPillarEl || !dayPillarEl || !hourPillarEl) return;

    const allPillars = {
        year: { el: document.getElementById('yearDoushou'), gan: yearPillarEl.textContent?.charAt(0) || '' },
        month: { el: document.getElementById('monthDoushou'), gan: monthPillarEl.textContent?.charAt(0) || '' },
        day: { el: document.getElementById('dayDoushou'), gan: dayPillarEl.textContent?.charAt(0) || '' },
        hour: { el: document.getElementById('hourDoushou'), gan: hourPillarEl.textContent?.charAt(0) || '' }
    };

    for (const [key, info] of Object.entries(allPillars)) {
        if (info.el && info.gan) {
            const result = calculateDoushouWuxing(mountainWuxing, info.gan);
            info.el.textContent = result.doushou;
            info.el.style.color = result.color;
        }
    }
}

function judgeSixPhaseLuck(mountain, dayGan, dayZhi) {
    const DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
    const sixPhaseResult = { luck: '平', sixPhase: [] };
    const shanGuaMap = {
        '壬': '未', '子': '未', '癸': '未',
        '丑': '戌', '艮': '戌', '寅': '戌',
        '甲': '丑', '卯': '丑', '乙': '丑',
        '辰': '辰', '巽': '辰', '巳': '辰',
        '丙': '未', '午': '未', '丁': '未',
        '未': '戌', '坤': '戌', '申': '戌',
        '庚': '丑', '酉': '丑', '辛': '丑',
        '戌': '辰', '乾': '辰', '亥': '辰'
    };
    const shangZhi = shanGuaMap[mountain];
    if (!shangZhi) return { luck: '平', sixPhase: [], message: '未知坐山' };
    const shangIndex = DIZHI.indexOf(shangZhi);
    const riZhiIndex = DIZHI.indexOf(dayZhi);
    if (shangIndex === -1 || riZhiIndex === -1) return { luck: '平', sixPhase: [], message: '未知地支' };
    const diff = (riZhiIndex - shangIndex + 12) % 12;
    if (diff === 0) return { luck: '大凶', sixPhase: ['六冲'], message: `六冲：${shangZhi}与${dayZhi}` };
    if (diff === 6) return { luck: '大吉', sixPhase: ['六合'], message: `六合：${shangZhi}与${dayZhi}` };
    return { luck: '平', sixPhase: ['平和'], message: '无冲合' };
}

// ======================== 演禽函数 ========================
async function updateYanqinDisplay(year, month, day) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/yanqin?year=${year}&month=${month}&day=${day}`);
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.result) {
                const dayYanqinEl = document.getElementById('dayYanqin');
                if (dayYanqinEl) dayYanqinEl.textContent = data.result.dayYanqin || '--';

                const yanqinDetail = document.getElementById('yanqinDetail');
                if (yanqinDetail) {
                    let detailHtml = '';
                    if (data.result.yearYanqin) detailHtml += `<div><span class="detail-label">年禽：</span><span>${data.result.yearYanqin}</span></div>`;
                    if (data.result.monthYanqin) detailHtml += `<div><span class="detail-label">月禽：</span><span>${data.result.monthYanqin}</span></div>`;
                    if (data.result.dayYanqin) detailHtml += `<div><span class="detail-label">日禽：</span><span>${data.result.dayYanqin}</span></div>`;
                    if (data.result.hourYanqin) detailHtml += `<div><span class="detail-label">时禽：</span><span>${data.result.hourYanqin}</span></div>`;
                    if (data.result.hostYanqin) detailHtml += `<div><span class="detail-label">值守禽：</span><span>${data.result.hostYanqin}</span></div>`;
                    if (data.result.jixing) detailHtml += `<div><span class="detail-label">吉星：</span><span style="color:#c41d7f;">${data.result.jixing}</span></div>`;
                    if (data.result.xiongxing) detailHtml += `<div><span class="detail-label">凶星：</span><span style="color:#666;">${data.result.xiongxing}</span></div>`;
                    yanqinDetail.innerHTML = detailHtml || '--';
                }
                return data.result;
            }
        }
    } catch (error) {
        console.error('演禽API调用失败，使用备用计算:', error);
    }
    return fallbackYanqinDisplay(year, month, day);
}

function fallbackYanqinDisplay(year, month, day) {
    const yanqinAnimals = ['角木蛟', '亢金龙', '氐土貉', '房日兔', '心月狐', '尾火虎', '箕水豹', '斗木獬', '牛金牛', '女土蝠', '虚日鼠', '危月燕', '室火猪', '壁水貐', '奎木狼', '娄金狗', '胃土雉', '昴日鸡', '毕月乌', '觜火猴', '参水猿', '井木犴', '鬼金羊', '柳土獐', '星日马', '张月鹿', '翼火蛇', '轸水蚓'];
    const dayOfYear = Math.floor((new Date(year, month - 1, day) - new Date(year, 0, 0)) / 86400000);
    const index = (year + dayOfYear) % 28;
    const animal = yanqinAnimals[index] || '--';
    const dayYanqinEl = document.getElementById('dayYanqin');
    if (dayYanqinEl) dayYanqinEl.textContent = animal;
    const yanqinDetail = document.getElementById('yanqinDetail');
    if (yanqinDetail) yanqinDetail.innerHTML = `<div><span class="detail-label">日禽(备用)：</span><span>${animal}</span></div>`;
    return { dayYanqin: animal };
}

// ======================== 占事函数 ========================
const ZHANSHI_CATEGORIES = {
    'general': '📋 占事总论',
    'stock': '📊 股市',
    'illness': '🏥 疾病',
    'travel': '🚗 出行',
    'career': '📈 前程',
    'marriage': '💑 婚姻',
    'wealth': '💰 财运',
    'litigation': '⚖️ 诉讼',
    'exam': '📝 考试',
    'lost': '🔍 失物',
    'child': '👶 子嗣',
    'house': '🏠 家宅',
    'business': '🏪 经营'
};

let _stockSearchTimer = null;
let _marketCache = null;
let _marketCacheTime = 0;

function onZhanshiCategoryChange() {
    const categorySelect = document.getElementById('zhanshiCategorySelect');
    const stockGroup = document.getElementById('stockCodeGroup');
    if (stockGroup) {
        const isStock = categorySelect && categorySelect.value === 'stock';
        stockGroup.style.display = isStock ? 'inline-block' : 'none';
        if (isStock) {
            fetchMarketOverview();
            setTimeout(() => document.getElementById('stockCodeInput').focus(), 100);
        }
    }
}

function onStockInputKeyDown(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        doSearchStock();
    }
}

async function doSearchStock() {
    const input = document.getElementById('stockCodeInput');
    const resultsDiv = document.getElementById('stockSearchResults');
    if (!input || !input.value.trim()) return;
    const keyword = input.value.trim();
    if (keyword.length < 2) {
        resultsDiv.innerHTML = '<span style="color:#999;">请输入至少2个字符</span>';
        return;
    }

    resultsDiv.innerHTML = '<span style="color:#999;">查询中...</span>';
    try {
        const resp = await fetch(`${API_BASE_URL}/api/stock/search?keyword=${encodeURIComponent(keyword)}`);
        const data = await resp.json();
        if (data.success && data.results && data.results.length > 0) {
            resultsDiv.innerHTML = data.results.map(r =>
                `<span style="cursor:pointer;color:#e65100;margin-right:10px;display:inline-block;padding:2px 6px;border:1px solid #ffe0b2;border-radius:4px;margin-bottom:4px;" onclick="selectStock('${r.code}','${r.name}')">${r.code} ${r.name}</span>`
            ).join('');
            if (data.results.length === 0) {
                resultsDiv.innerHTML = '<span style="color:#999;">未找到匹配股票</span>';
            }
        } else {
            resultsDiv.innerHTML = '<span style="color:#999;">未找到匹配股票</span>';
        }
    } catch (e) {
        resultsDiv.innerHTML = '<span style="color:#e53935;">查询失败，请检查网络</span>';
    }
}

function searchStock() {
    if (_stockSearchTimer) clearTimeout(_stockSearchTimer);
    _stockSearchTimer = setTimeout(doSearchStock, 300);
}

function selectStock(code, name) {
    document.getElementById('stockCodeInput').value = `${code} ${name}`;
    document.getElementById('stockSearchResults').innerHTML = `<span style="color:#2e7d32;font-weight:bold;">已选择: ${code} ${name}</span>`;
}

async function fetchMarketOverview() {
    const container = document.getElementById('marketOverview');
    if (!container) return;
    const now = Date.now();
    if (_marketCache && now - _marketCacheTime < 30000) {
        container.innerHTML = _marketCache;
        return;
    }
    container.innerHTML = '<span style="color:#999;">获取大盘行情...</span>';
    try {
        const resp = await fetch(`${API_BASE_URL}/api/stock/market`);
        const data = await resp.json();
        if (data.success && data.market) {
            const m = data.market;
            let html = '<div style="font-size:13px;background:#f5f5f5;padding:8px;border-radius:6px;margin-top:6px;">';
            html += '<strong>📊 大盘指数</strong><div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-top:4px;">';
            if (Array.isArray(m)) {
                m.slice(0, 4).forEach(idx => {
                    const c = (idx.change || 0) >= 0 ? '#e53935' : '#43a047';
                    const icon = (idx.change || 0) >= 0 ? '📈' : '📉';
                    html += `<div>${icon} <span style="color:#888;">${idx.name||idx.code||''}</span> <span style="color:${c};font-weight:bold;">${idx.price||'--'}</span> <span style="color:${c};">${(idx.change||0) > 0 ? '+' : ''}${idx.change||'--'}%</span></div>`;
                });
            } else if (m.name) {
                const c = (m.change || 0) >= 0 ? '#e53935' : '#43a047';
                const icon = (m.change || 0) >= 0 ? '📈' : '📉';
                html += `<div>${icon} <span style="color:#888;">${m.name}</span> <span style="color:${c};font-weight:bold;">${m.price||'--'}</span> <span style="color:${c};">${(m.change||0) > 0 ? '+' : ''}${m.change||'--'}%</span></div>`;
            }
            html += '</div></div>';
            container.innerHTML = html;
            _marketCache = html;
            _marketCacheTime = now;
        } else {
            container.innerHTML = '';
        }
    } catch (e) {
        container.innerHTML = '';
    }
}

function handleStartZhanshi() {
    const categorySelect = document.getElementById('zhanshiCategorySelect');
    const category = categorySelect ? categorySelect.value : 'general';
    const categoryName = categorySelect ? categorySelect.options[categorySelect.selectedIndex].text : '📋 占事总论';

    let stockCode = '';
    if (category === 'stock') {
        const stockInput = document.getElementById('stockCodeInput');
        if (stockInput && stockInput.value.trim()) {
            const match = stockInput.value.trim().match(/^(\d{6})/);
            if (match) stockCode = match[1];
        }
    }

    // 获取求测人信息（增强版）
    const qiucerenInfo = {
        gender: document.getElementById('qiucerenGender')?.value || '',
        age: parseInt(document.getElementById('qiucerenAge')?.value) || 0,
        occupation: document.getElementById('qiucerenOccupation')?.value || '',
        residence: document.getElementById('qiucerenResidence')?.value || '',
        era: document.getElementById('qiucerenEra')?.value || ''
    };

    startZhanshiCalculation(category, categoryName, stockCode, qiucerenInfo);
}

async function startZhanshiCalculation(category, categoryName, stockCode, qiucerenInfo = {}) {
    const dateInput = document.getElementById('zhanshiDateInput');
    const timeInput = document.getElementById('zhanshiTimeInput');
    if (!dateInput || !dateInput.value) {
        alert('请选择占事日期');
        return;
    }
    const date = new Date(dateInput.value);
    let hour = 12, minute = 0;
    if (timeInput && timeInput.value) {
        const parts = timeInput.value.split(':');
        hour = parseInt(parts[0]) || 12;
        minute = parseInt(parts[1]) || 0;
    }
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();

    try {
        let stockQuote = null;
        if (category === 'stock' && stockCode) {
            try {
                const quoteResp = await fetch(`${API_BASE_URL}/api/stock/quote?code=${stockCode}`);
                const quoteData = await quoteResp.json();
                if (quoteData.success) stockQuote = quoteData.quote;
            } catch (e) {
                console.warn('获取股票行情失败，跳过');
            }
        }

        const sizhuResponse = await fetch(`${API_BASE_URL}/api/sizhu?year=${year}&month=${month}&day=${day}&hour=${hour}`);
        if (!sizhuResponse.ok) throw new Error('四柱API请求失败');
        const sizhuResult = await sizhuResponse.json();
        if (!sizhuResult.success || !sizhuResult.sizhu) throw new Error(sizhuResult.error || '四柱计算失败');

        const sz = sizhuResult.sizhu;
        const dayGan = sz.dayGan;
        const dayZhi = sz.dayZhi;
        const result = await daLiuRenPaiPan(year, month, day, hour, minute, dayGan, dayZhi);
        if (result) {
            displayZhanshiResult({
                category, categoryName,
                year, month, day, hour, minute, dayGan, dayZhi,
                yearZhi: sz.yearZhi,
                monthZhi: sz.monthZhi,
                sizhu: `${sz.yearPillar} ${sz.monthPillar} ${sz.dayPillar} ${sz.hourPillar}`,
                paipan: result,
                stockCode, stockQuote,
                qiucerenInfo: qiucerenInfo
            });

            // 增强版：获取类象分析和应期判断
            fetchEnhancedAnalysis({
                category, categoryName,
                year, month, day, hour,
                dayGan, dayZhi,
                yearZhi: sz.yearZhi,
                monthZhi: sz.monthZhi,
                siKe: result.siKe,
                sanChuan: result.sanChuan,
                sanChuanTianJiang: result.sanChuanTianJiang,
                qiucerenInfo: qiucerenInfo
            });

            if (category === 'stock' && stockCode) {
                const sizhuStr = `${sz.yearPillar} ${sz.monthPillar} ${sz.dayPillar} ${sz.hourPillar}`;
                const siKeObj = result.siKe || {};
                const sikeStr = [siKeObj.ke1, siKeObj.ke2, siKeObj.ke3, siKeObj.ke4]
                    .filter(Boolean).map(k => `${k.top||k.shangGan||''}${k.zhi||k.shangZhi||''} / ${k.bottom||k.xiaGan||''}${k.zhi||k.xiaZhi||''}`)
                    .join(' | ');
                const sanChuanObj = result.sanChuan || {};
                const sanchuanStr = [sanChuanObj.chuChuan, sanChuanObj.zhongChuan, sanChuanObj.moChuan]
                    .filter(Boolean).join(' → ');

                appendAIJudgeResult('loading');
                fetch(`${API_BASE_URL}/api/ai/zhanshi_judge`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        sizhu: sizhuStr,
                        sike: sikeStr,
                        sanchuan: sanchuanStr,
                        keti: result.keTi || '',
                        zhanshi: 'stock',
                        stock_code: stockCode
                    })
                })
                .then(r => r.json())
                .then(judgeData => {
                    if (judgeData.success && judgeData.result) {
                        appendAIJudgeResult(judgeData.result);
                    } else {
                        appendAIJudgeResult('AI判断暂不可用，请稍后重试');
                    }
                })
                .catch(() => appendAIJudgeResult('AI判断请求失败，请检查网络'));
            }
        } else {
            alert('排盘失败，请检查输入');
        }
    } catch (error) {
        console.error('占事计算失败:', error);
        alert('占事计算失败: ' + error.message);
    }
}

async function fetchEnhancedAnalysis(data) {
    try {
        // P3（2026-08-18）：占事断语统一走 /api/liuren/zhanshi_duanyu（按占事专断，非一刀切）
        const response = await fetch(`${API_BASE_URL}/api/liuren/zhanshi_duanyu`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                category: data.category || '',
                zhanshi: data.categoryName || '',
                year: data.year, month: data.month, day: data.day, hour: data.hour,
                dayGan: data.dayGan, dayZhi: data.dayZhi
            })
        });
        const result = await response.json();
        if (result.success) {
            displayEnhancedAnalysis(result.data);
        } else {
            console.error('占事断语接口:', result.error);
        }
    } catch (error) {
        console.error('获取占事断语失败:', error);
    }
}

function displayEnhancedAnalysis(data) {
    // P3：占事断语展示（课体断语 + 占类专断 + 毕法）
    const dyContent = document.getElementById('zhanshiDuanyuContent');
    if (dyContent) {
        let dyHtml = '';
        if (data.summary) dyHtml += `<div style="margin-bottom:8px;"><strong>📌 综合断语：</strong>${data.summary}</div>`;
        if (data.level) dyHtml += `<div style="margin-bottom:8px;"><strong>评级：</strong><span style="color:#c62828;">${data.level}</span></div>`;
        const kt = (data.paipan && data.paipan.keti) || '';
        if (data.keti_duanyu) dyHtml += `<div style="margin-bottom:8px;"><strong>课体${kt ? '（' + kt + '）' : ''}：</strong>${data.keti_duanyu}</div>`;
        if (data.zhanshi_duanyu && data.zhanshi_duanyu.length > 0) {
            dyHtml += `<div style="margin-bottom:6px;"><strong>占事专断（${data.zhanshi || '总论'}）：</strong></div><ul style="margin:4px 0 8px 20px;padding:0;">`;
            data.zhanshi_duanyu.forEach(d => { dyHtml += `<li>${d}</li>`; });
            dyHtml += `</ul>`;
        }
        if (data.bifa_duanyu && data.bifa_duanyu.length > 0) {
            dyHtml += `<div style="margin-bottom:6px;"><strong>毕法：</strong></div><ul style="margin:4px 0 8px 20px;padding:0;">`;
            data.bifa_duanyu.slice(0, 3).forEach(d => { dyHtml += `<li>${d}</li>`; });
            dyHtml += `</ul>`;
        }
        dyContent.innerHTML = dyHtml || `<div style="color:#888;">暂无可展示断语</div>`;
    }

    // 显示求测人信息
    const qiucerenDisplay = document.getElementById('qiucerenInfoDisplay');
    if (qiucerenDisplay && data.qiucerenInfo) {
        const info = data.qiucerenInfo;
        let html = `<h4 style="color:#e65100;font-size:16px;margin-bottom:10px;">👤 求测人信息</h4>`;
        if (info.gender) html += `<div><strong>性别：</strong>${info.gender}</div>`;
        if (info.age) html += `<div><strong>年龄：</strong>${info.age}岁</div>`;
        if (info.occupation) html += `<div><strong>职业：</strong>${info.occupation}</div>`;
        if (info.residence) html += `<div><strong>居住：</strong>${info.residence}</div>`;
        if (info.era) html += `<div><strong>时代：</strong>${info.era}</div>`;
        if (!info.gender && !info.age && !info.occupation && !info.residence && !info.era) {
            html += `<div style="color:#888;">未填写求测人信息（填写可获得更精准分析）</div>`;
        }
        qiucerenDisplay.innerHTML = html;
    }

    // 显示类象分析
    const leixiangContent = document.getElementById('leixiangContent');
    if (leixiangContent && data.classifications) {
        let html = '';
        for (const [zhi, cls] of Object.entries(data.classifications)) {
            html += `<div style="margin-bottom:10px;"><strong>${zhi}：</strong>`;
            if (cls.contextual && cls.contextual.length > 0) {
                html += `${cls.contextual.join('、')}`;
            } else {
                html += `基础类象分析`;
            }
            html += `</div>`;
        }
        leixiangContent.innerHTML = html || `<div style="color:#888;">暂无类象分析数据</div>`;
    }

    // 显示应期分析
    const yingqiContent = document.getElementById('yingqiContent');
    if (yingqiContent && data.yingqi) {
        let html = '';
        if (data.yingqi.ke_ti && data.yingqi.ke_ti.length > 0) {
            html += `<div style="margin-bottom:10px;"><strong>课体课格：</strong>${data.yingqi.ke_ti.join('、')}</div>`;
        }
        if (data.yingqi.xun_kong) {
            html += `<div style="margin-bottom:10px;"><strong>旬空：</strong>${data.yingqi.xun_kong}</div>`;
        }
        if (data.yingqi.dizhi_shu_yingqi && data.yingqi.dizhi_shu_yingqi.length > 0) {
            html += `<div style="margin-bottom:10px;"><strong>地支数应期：</strong>`;
            for (const yq of data.yingqi.dizhi_shu_yingqi) {
                html += `${yq.basis}=${yq.total}年(${yq.meaning})`;
            }
            html += `</div>`;
        }
        if (data.yingqi.xing_nian_yingqi && data.yingqi.xing_nian_yingqi.length > 0) {
            html += `<div style="margin-bottom:10px;"><strong>行年应期：</strong>`;
            for (const yq of data.yingqi.xing_nian_yingqi) {
                html += `${yq.meaning}`;
            }
            html += `</div>`;
        }
        yingqiContent.innerHTML = html || `<div style="color:#888;">暂无应期分析数据</div>`;
    }
}

function displayZhanshiResult(data) {
    const modal = document.getElementById('zhanshiResultModal');
    const content = document.getElementById('zhanshiResultContent');
    if (!modal || !content) return;

    const result = data.paipan;
    let html = `<div class="zhanshi-result-header">
        <h3>占事结果 · ${data.categoryName || '📋 占事总论'}</h3>
        <div style="margin: 10px 0; color: #666;">${data.year}年${data.month}月${data.day}日 - 四柱：${data.sizhu}</div>
    </div>`;

    if (data.category === 'stock' && data.stockQuote) {
        const q = data.stockQuote;
        const changeColor = q.change >= 0 ? '#e53935' : '#43a047';
        const changeIcon = q.change >= 0 ? '📈' : '📉';
        html += `<div class="zhanshi-section" style="background:linear-gradient(135deg,#fff8e1,#fff3e0);border:2px solid #ffb74d;border-radius:8px;padding:12px;margin-bottom:12px;">
            <h4 style="margin:0 0 8px 0;">${changeIcon} 实时行情 · ${q.name || data.stockCode}</h4>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:14px;">
                <div><strong>最新价：</strong>${q.price}</div>
                <div style="color:${changeColor};font-weight:bold;"><strong>涨跌幅：</strong>${q.change > 0 ? '+' : ''}${q.change}%</div>
                <div><strong>最高：</strong>${q.high}</div>
                <div><strong>最低：</strong>${q.low}</div>
                <div><strong>开盘：</strong>${q.open}</div>
                <div><strong>昨收：</strong>${q.prev_close}</div>
                <div><strong>成交额：</strong>${q.amount ? (q.amount/1e8).toFixed(2) + '亿' : '--'}</div>
                <div><strong>换手率：</strong>${q.turnover_rate || '--'}%</div>
            </div>
            <div style="margin-top:8px;font-size:13px;padding:6px;border-radius:4px;background:rgba(255,255,255,0.7);">
                <strong>六壬股市提示：</strong> 以下排盘结合实时行情可综合研判该股短期走势
            </div>
        </div>`;
    }

    html += `<div class="zhanshi-section"><h4>天地盘</h4><div class="tiandipan-display">`;
    const tianPan = result.tianPan;
    const diPan = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
    const tianPanDisplay = {};
    if (typeof tianPan === 'object') {
        if (Array.isArray(tianPan)) {
            for (let i = 0; i < diPan.length; i++) {
                tianPanDisplay[diPan[i]] = tianPan[i] || '';
            }
        } else {
            Object.assign(tianPanDisplay, tianPan);
        }
    }
    html += `<table class="tiandipan-table">`;
    html += `<tr><td></td><td>巳(${tianPanDisplay['巳']||''})</td><td>午(${tianPanDisplay['午']||''})</td><td>未(${tianPanDisplay['未']||''})</td><td>申(${tianPanDisplay['申']||''})</td><td></td></tr>`;
    html += `<tr><td>辰(${tianPanDisplay['辰']||''})</td><td></td><td></td><td></td><td></td><td>酉(${tianPanDisplay['酉']||''})</td></tr>`;
    html += `<tr><td>卯(${tianPanDisplay['卯']||''})</td><td></td><td></td><td></td><td></td><td>戌(${tianPanDisplay['戌']||''})</td></tr>`;
    html += `<tr><td>寅(${tianPanDisplay['寅']||''})</td><td></td><td></td><td></td><td></td><td>亥(${tianPanDisplay['亥']||''})</td></tr>`;
    html += `<tr><td></td><td>丑(${tianPanDisplay['丑']||''})</td><td>子(${tianPanDisplay['子']||''})</td><td></td><td></td><td></td></tr>`;
    html += `</table>`;
    html += `</div></div>`;

    html += `<div class="zhanshi-section"><h4>四课</h4>`;
    const siKeObj = result.siKe;
    if (siKeObj) {
        html += `<div class="sike-display">`;
        const siKeArray = [siKeObj.ke1, siKeObj.ke2, siKeObj.ke3, siKeObj.ke4];
        for (const ke of siKeArray) {
            if (!ke) continue;
            html += `<div class="sike-item"><span class="sike-tiangan">${ke.top||ke.shangGan||ke.tianGan||''}</span><span class="sike-dizhi">${ke.zhi||ke.shangZhi||ke.tianZhi||''}</span></div>
                <div class="sike-item"><span class="sike-tiangan">${ke.bottom||ke.xiaGan||ke.diGan||''}</span><span class="sike-dizhi">${ke.zhi||ke.xiaZhi||ke.diZhi||''}</span></div>`;
        }
        html += `</div>`;
    }
    html += `</div>`;

    html += `<div class="zhanshi-section"><h4>三传</h4><div class="sanchuan-display">`;
    const sanChuan = result.sanChuan;
    const chuanZhi = sanChuan ? [sanChuan.chuChuan, sanChuan.zhongChuan, sanChuan.moChuan] : [];
    const chuanTianJiang = result.sanChuanTianJiang || [];
    const chuanLiuqin = result.sanChuanLiuqin || [];
    const labels = ['初传', '中传', '末传'];
    for (let i = 0; i < 3; i++) {
        const zhi = chuanZhi[i] || '';
        const tianJiang = chuanTianJiang[i] || '';
        const liuQin = chuanLiuqin[i] || '';
        html += `<div class="chuan-item"><span class="chuan-label">${labels[i]}</span><span>${liuQin} ${tianJiang} ${zhi}</span></div>`;
    }
    html += `</div></div>`;

    if (result.keTi) {
        html += `<div class="zhanshi-section"><h4>课体</h4><div class="keti-display">${result.keTi}</div></div>`;
    }

    // ========== 神煞展示 ==========
    if (data.yearZhi && data.monthZhi) {
        const shenSha = calculateAllShenSha(data.dayGan, data.dayZhi, data.yearZhi, data.monthZhi);
        const hasNian = Object.keys(shenSha.nianSha).length > 0;
        const hasYue = Object.keys(shenSha.yueSha).length > 0;
        const hasRi = Object.keys(shenSha.riSha).length > 0;

        if (hasNian || hasYue || hasRi) {
            html += `<div class="zhanshi-section"><h4>神煞</h4>`;

            if (hasNian) {
                html += `<div class="shensha-category"><h5>年煞（${data.yearZhi}）</h5><div class="guiren-shensha">`;
                for (const [name, value] of Object.entries(shenSha.nianSha)) {
                    html += `<div class="shensha-item"><span class="shensha-label">${name}</span><span class="shensha-value">${value}</span></div>`;
                }
                html += `</div></div>`;
            }

            if (hasYue) {
                html += `<div class="shensha-category"><h5>月煞（${data.monthZhi}）</h5><div class="guiren-shensha">`;
                for (const [name, value] of Object.entries(shenSha.yueSha)) {
                    html += `<div class="shensha-item"><span class="shensha-label">${name}</span><span class="shensha-value">${value}</span></div>`;
                }
                html += `</div></div>`;
            }

            if (hasRi) {
                html += `<div class="shensha-category"><h5>日煞（${data.dayGan}${data.dayZhi}）</h5><div class="guiren-shensha">`;
                for (const [name, value] of Object.entries(shenSha.riSha)) {
                    html += `<div class="shensha-item"><span class="shensha-label">${name}</span><span class="shensha-value">${value}</span></div>`;
                }
                html += `</div></div>`;
            }

            html += `</div>`;
        }
    }

    const daliurenZhanshiResult = document.getElementById('daliurenZhanshiResult');
    if (daliurenZhanshiResult) daliurenZhanshiResult.innerHTML = html;

    modal.style.display = 'block';
}

function appendAIJudgeResult(result) {
    const container = document.getElementById('daliurenZhanshiResult');
    const existing = document.getElementById('aiJudgeResult');
    if (existing) existing.remove();

    if (result === 'loading') {
        const div = document.createElement('div');
        div.id = 'aiJudgeResult';
        div.innerHTML = `<div class="zhanshi-section" style="background:#f3e5f5;border:1px solid #ce93d8;border-radius:8px;padding:12px;margin-top:12px;text-align:center;">
            <span style="color:#7b1fa2;">🧠 六壬股市综合分析中...</span>
        </div>`;
        container.appendChild(div);
        return;
    }

    const div = document.createElement('div');
    div.id = 'aiJudgeResult';
    div.innerHTML = `<div class="zhanshi-section" style="background:linear-gradient(135deg,#f3e5f5,#e8f5e9);border:2px solid #7b1fa2;border-radius:8px;padding:12px;margin-top:12px;">
        <h4 style="margin:0 0 8px 0;color:#4a148c;">🧠 六壬股市综合分析 · AI判读</h4>
        <div style="font-size:14px;line-height:1.8;white-space:pre-wrap;color:#333;">${result}</div>
    </div>`;
    container.appendChild(div);
}

function closeZhanshiResult() {
    const modal = document.getElementById('zhanshiResultModal');
    if (modal) modal.style.display = 'none';
}

// ======================== UI辅助函数 ========================
function getScoreColor(score) {
    if (score >= 85) return '#c41d7f';
    if (score >= 70) return '#1890ff';
    if (score >= 60) return '#faad14';
    return '#ff4d4f';
}

function getDuanyu(ketiName) {
    if (!ketiName) return '--';
    const duanyuMap = {
        '元首': '事多顺利，吉', '重审': '反复不定，中', '知一': '事有专一，吉',
        '涉害': '事有阻碍，凶', '遥克': '远事难成，中', '昴星': '事多暗昧，凶',
        '别责': '事有反复，中', '八专': '事多专一，平', '伏吟': '事多停滞，凶',
        '反吟': '事多反复，凶'
    };
    for (const [key, value] of Object.entries(duanyuMap)) {
        if (ketiName.includes(key)) return value;
    }
    return '--';
}

// ======================== 初始化函数 ========================
function initZuoshanDropdown() {
    const optionsContainer = document.getElementById('zuoshanOptions');
    if (!optionsContainer) return;
    if (optionsContainer.children.length > 0) return;

    YNZR.data.baguaOrder.forEach(bagua => {
        const mountainGroup = YNZR.data.ershisiShanxiang[bagua];
        if (!mountainGroup?.mountains) return;

        const groupDiv = document.createElement('div');
        groupDiv.className = 'dropdown-group';
        groupDiv.textContent = `${bagua}卦 (${mountainGroup.element})`;
        optionsContainer.appendChild(groupDiv);

        mountainGroup.mountains.forEach(mtn => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'dropdown-option';
            optionDiv.dataset.value = mtn.name;
            optionDiv.dataset.element = mountainGroup.element;
            optionDiv.dataset.color = mountainGroup.color;
            optionDiv.dataset.bagua = bagua;
            optionDiv.dataset.opposite = mtn.opposite;
            optionDiv.innerHTML = `<strong>${mtn.name}</strong> <span style="color: #999; font-size: 12px;">(${mtn.pinyin}) - ${bagua}卦</span>`;
            optionDiv.addEventListener('click', function(e) {
                e.stopPropagation();
                selectZuoshan(this);
            });
            optionsContainer.appendChild(optionDiv);
        });
    });

    const display = document.getElementById('zuoshanSelectDisplay');
    const dropdown = document.getElementById('zuoshanDropdown');
    if (display && dropdown) {
        display.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdown.classList.toggle('show');
            if (dropdown.classList.contains('show')) {
                const searchInput = document.getElementById('zuoshanSearch');
                if (searchInput) setTimeout(() => searchInput.focus(), 50);
            }
        });
        document.addEventListener('click', function(e) {
            if (!dropdown.contains(e.target) && e.target !== display) {
                dropdown.classList.remove('show');
            }
        });
    }

    const searchInput = document.getElementById('zuoshanSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            document.querySelectorAll('.dropdown-option').forEach(opt => {
                const text = opt.textContent.toLowerCase();
                opt.classList.toggle('hidden', !text.includes(searchTerm));
            });
        });
        searchInput.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
}

function initLailongDropdown() {
    const container = document.getElementById('lailongDropdown');
    if (!container) return;
    container.innerHTML = '';
    const items = ['壬龙', '子龙', '癸龙', '丑龙', '艮龙', '寅龙', '甲龙', '卯龙', '乙龙', '辰龙', '巽龙', '巳龙',
        '丙龙', '午龙', '丁龙', '未龙', '坤龙', '申龙', '庚龙', '酉龙', '辛龙', '戌龙', '乾龙', '亥龙'];
    items.forEach(name => {
        const item = document.createElement('div');
        item.className = 'zuoshan-item';
        item.dataset.value = name;
        item.textContent = name;
        item.addEventListener('click', () => {
            const display = document.getElementById('lailongSelectDisplay');
            const hidden = document.getElementById('lailongSelect');
            if (display) {
                display.textContent = name;
                display.dataset.value = name;
            }
            if (hidden) hidden.value = name;
            document.getElementById('lailongDropdown').classList.remove('active');
        });
        container.appendChild(item);
    });
}

function getDouShouShanElement() {
    const zuoshanDisplay = document.getElementById('zuoshanSelectDisplay');
    return zuoshanDisplay?.dataset?.mountainElement || null;
}

function selectZuoshan(item) {
    const display = document.getElementById('zuoshanSelectDisplay');
    if (display) {
        display.innerHTML = `<span>${item.dataset.value}山</span>`;
        display.dataset.value = item.dataset.value;
        display.dataset.mountainElement = item.dataset.element;
        display.dataset.mountainColor = item.dataset.color;
        display.dataset.bagua = item.dataset.bagua;
        display.dataset.opposite = item.dataset.opposite;
    }
    document.querySelectorAll('.dropdown-option').forEach(opt => {
        opt.classList.remove('selected');
        if (opt.dataset.value === item.dataset.value) {
            opt.classList.add('selected');
        }
    });
    document.getElementById('zuoshanDropdown')?.classList.remove('show');

    const mountainName = item.dataset.value;
    const xiangshan = YNZR.data.zuixiangPairs[mountainName];
    const xiangshanDisplay = document.getElementById('xiangshanDisplay');
    if (xiangshanDisplay && xiangshan) {
        xiangshanDisplay.textContent = `${xiangshan}向`;
    }
    const shanxiangEl = document.getElementById('shanxiang');
    if (shanxiangEl && xiangshan) {
        shanxiangEl.value = `${mountainName}山${xiangshan}向`;
    }

    const zuoshan = YNZR.getCurrentMountain();
    if (zuoshan && currentFourPillars) {
        const doushouScoreEl = document.getElementById('doushouScore');
        if (doushouScoreEl && doushouScoreEl.textContent !== '--') {
            updateDoushouDisplay(item.dataset.element);
        }
    }
}

// ==================== 龙运吉凶计算 ====================
function calculateLongLuck(mountain, year) {
    const stemIndex = (year - 4) % 10;
    const stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
    const stem = stems[stemIndex >= 0 ? stemIndex : stemIndex + 10];
    const stemElements = { '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水' };
    const stemElement = stemElements[stem] || '土';

    let mountainElement = null;
    for (const bagua of Object.values(YNZR.data.ershisiShanxiang)) {
        const found = bagua.mountains.find(m => m.name === mountain);
        if (found) { mountainElement = bagua.element; break; }
    }
    if (!mountainElement) {
        return { score: 60, color: '#888888', level: '平', desc: `未知山向「${mountain}」，无法计算龙运。` };
    }

    const sheng = { '木': '火', '火': '土', '土': '金', '金': '水', '水': '木' };
    const ke = { '木': '土', '土': '水', '水': '火', '火': '金', '金': '木' };

    if (sheng[mountainElement] === stemElement) {
        return { score: 95, color: '#1b5e20', level: '大吉', desc: `${mountain}山属${mountainElement}，流年天干${stem}属${stemElement}，山生年干，龙运亨通。` };
    } else if (sheng[stemElement] === mountainElement) {
        return { score: 85, color: '#2e7d32', level: '吉', desc: `${mountain}山属${mountainElement}，流年天干${stem}属${stemElement}，年干生山，龙运兴旺。` };
    } else if (ke[mountainElement] === stemElement) {
        return { score: 65, color: '#f57f17', level: '平', desc: `${mountain}山属${mountainElement}，流年天干${stem}属${stemElement}，山克年干，龙运平顺。` };
    } else if (ke[stemElement] === mountainElement) {
        return { score: 45, color: '#c62828', level: '小凶', desc: `${mountain}山属${mountainElement}，流年天干${stem}属${stemElement}，年干克山，龙运受阻。` };
    }
    return { score: 75, color: '#558b2f', level: '中吉', desc: `${mountain}山属${mountainElement}，流年天干${stem}属${stemElement}，干支比和，龙运稳定。` };
}

// ==================== 流年吉凶计算 ====================
function calculateLiunian(year, month, day, lailong) {
    if (!lailong || !year || !month || !day) {
        return;
    }
    const mountain = lailong.replace('龙', '');
    const liunianResult = calculateLongLuck(mountain, year);
    if (!liunianResult) {
        console.error('龙运计算失败');
        return;
    }
    const liunianSection = document.getElementById('liunianSection');
    if (liunianSection) {
        const liunianContent = document.getElementById('liunianContent');
        if (liunianContent) {
            liunianContent.innerHTML = `
                <div class="result-row">
                    <div class="result-label">来龙</div>
                    <div class="result-value">${lailong}</div>
                </div>
                <div class="result-row">
                    <div class="result-label">流年日期</div>
                    <div class="result-value">${year}年${month}月${day}日</div>
                </div>
                <div class="result-row">
                    <div class="result-label">流年评分</div>
                    <div class="score-display">${liunianResult.score}分</div>
                </div>
                <div class="result-row">
                    <div class="result-label">吉凶等级</div>
                    <div class="result-value" style="color: ${liunianResult.color}">${liunianResult.level}</div>
                </div>
                <div class="result-row">
                    <div class="result-label">分析</div>
                    <div class="result-value">${liunianResult.desc}</div>
                </div>
            `;
        }
        liunianSection.classList.add('show');
    }
    updateAIEvaluation();
}

// ==================== 进度条功能 ====================
let progressInterval = null;
let progressContainerElement = null;

function createProgressElements() {
    if (document.getElementById('progressContainer')) {
        return;
    }
    const progressContainer = document.createElement('div');
    progressContainer.id = 'progressContainer';
    progressContainer.className = 'progress-container';
    progressContainer.style.display = 'none';

    const progressMessage = document.createElement('div');
    progressMessage.className = 'progress-message';
    progressMessage.textContent = '正在进行择日计算，请稍候...';

    const progressBarWrapper = document.createElement('div');
    progressBarWrapper.className = 'progress-bar-wrapper';

    const progressBar = document.createElement('div');
    progressBar.id = 'progressBar';
    progressBar.className = 'progress-bar';
    progressBarWrapper.appendChild(progressBar);

    const progressStatus = document.createElement('div');
    progressStatus.id = 'progressStatus';
    progressStatus.className = 'progress-status';
    progressStatus.textContent = '0%';

    progressContainer.appendChild(progressMessage);
    progressContainer.appendChild(progressBarWrapper);
    progressContainer.appendChild(progressStatus);

    const inputSection = document.querySelector('.input-section');
    if (inputSection && inputSection.parentNode) {
        inputSection.parentNode.insertBefore(progressContainer, inputSection.nextSibling);
    }
    progressContainerElement = progressContainer;
}

function showProgress() {
    createProgressElements();
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressStatus = document.getElementById('progressStatus');

    if (progressContainer) {
        progressContainer.style.display = 'block';
    }
    if (progressBar) {
        progressBar.style.width = '0%';
    }
    if (progressStatus) {
        progressStatus.textContent = '0%';
    }

    let currentProgress = 0;
    progressInterval = setInterval(() => {
        if (currentProgress < 90) {
            currentProgress += Math.random() * 5;
            if (currentProgress > 90) currentProgress = 90;
            updateProgress(currentProgress);
        }
    }, 300);
}

function updateProgress(percent) {
    const progressBar = document.getElementById('progressBar');
    const progressStatus = document.getElementById('progressStatus');
    if (progressBar) {
        progressBar.style.width = `${Math.min(percent, 100)}%`;
    }
    if (progressStatus) {
        progressStatus.textContent = `${Math.round(Math.min(percent, 100))}%`;
    }
}

function hideProgress() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    updateProgress(100);
    setTimeout(() => {
        const progressContainer = document.getElementById('progressContainer');
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
        const progressBar = document.getElementById('progressBar');
        if (progressBar) {
            progressBar.style.width = '0%';
        }
        const progressStatus = document.getElementById('progressStatus');
        if (progressStatus) {
            progressStatus.textContent = '0%';
        }
    }, 500);
}

// ==================== 开始择日 ====================
async function startZeri() {
    const zetiriTypeSelect = document.getElementById('zetiriTypeSelect');
    const typeValue = zetiriTypeSelect ? zetiriTypeSelect.value : '';
    if (!typeValue) {
        alert('请先选择择日类型（立碑、安葬、婚嫁或开业）！');
        return;
    }

    let currentMountain = null;
    if (typeValue === '婚嫁') {
        const nanNianmingSelect = document.getElementById('nanNianmingSelect');
        if (nanNianmingSelect && nanNianmingSelect.value) {
            currentMountain = nanNianmingSelect.value.split(' ')[0];
        }
        if (!currentMountain) {
            alert('请选择男年命！');
            return;
        }
    } else {
        currentMountain = YNZR.getCurrentMountain();
        if (!currentMountain) {
            alert('请选择坐山！');
            return;
        }
    }

    const jiriCountEl = document.getElementById('jiriCount');
    const jiriCount = jiriCountEl ? parseInt(jiriCountEl.value) : 5;

    const startYearEl = document.getElementById('startYear');
    const startMonthEl = document.getElementById('startMonth');
    const startDayEl = document.getElementById('startDay');
    const endYearEl = document.getElementById('endYear');

    if (!startYearEl || !startMonthEl || !startDayEl) {
        alert('请设置起始日期！');
        return;
    }

    const startDate = new Date(
        startYearEl.value || new Date().getFullYear(),
        (startMonthEl.value || 1) - 1,
        startDayEl.value || 1
    );

    let endDate;
    if (endYearEl && endYearEl.value) {
        const endMonthEl = document.getElementById('endMonth');
        const endDayEl = document.getElementById('endDay');
        endDate = new Date(
            endYearEl.value,
            (endMonthEl.value || 1) - 1,
            endDayEl.value || 1
        );
    } else {
        endDate = new Date(startDate);
        endDate.setFullYear(endDate.getFullYear() + 3);
    }

    if (startDate > endDate) {
        alert('起始日期不能晚于结束日期，请检查日期设置！');
        return;
    }

    showProgress();

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);
        const apiCheckResponse = await fetch(API_BASE_URL + '/api/sizhu?year=2026&month=3&day=29&hour=12', {
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        if (!apiCheckResponse.ok) {
            throw new Error('API服务器未响应');
        }
        generateJiriList(startDate, endDate, jiriCount);
    } catch (error) {
        const progressContainer = document.getElementById('progressContainer');
        const progressMessage = progressContainer?.querySelector('.progress-message');
        if (progressMessage) {
            progressMessage.textContent = '正在启动API服务器，请稍候...';
        }
        setTimeout(async () => {
            try {
                const retryResponse = await fetch(API_BASE_URL + '/api/sizhu?year=2026&month=3&day=29&hour=12', {
                    timeout: 5000
                });
                if (retryResponse.ok) {
                    if (progressMessage) {
                        progressMessage.textContent = 'API服务器已启动，正在分析日期...';
                    }
                    generateJiriList(startDate, endDate, jiriCount);
                } else {
                    hideProgress();
                    alert('API服务器启动失败，请运行 start_api_server.bat 后重试');
                }
            } catch (retryError) {
                hideProgress();
                alert('API服务器未运行，请先运行 start_api_server.bat 启动服务器');
            }
        }, 2000);
    }
}

// ==================== 显示筛选后的日期列表 ====================
function displayFilteredDates(filteredDates, classification) {
    const dateListEl = document.getElementById('dateList');
    if (!dateListEl) return;
    dateListEl.innerHTML = '';

    if (!filteredDates || filteredDates.length === 0) {
        dateListEl.innerHTML = '<div style="padding: 40px; text-align: center; color: #999;">未找到符合条件的吉课</div>';
        return;
    }

    const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];

    filteredDates.forEach((dateData, index) => {
        const { year, month, day, hour, hourName, score, level, modules } = dateData;
        const date = new Date(year, month - 1, day);
        const weekDay = weekDays[date.getDay()];

        let lunarText = '--';
        if (typeof LunarCalendarExt !== 'undefined') {
            const lunarDate = LunarCalendarExt.solarToLunar(year, month, day);
            if (lunarDate) {
                lunarText = LunarCalendarExt.formatLunarDate(lunarDate);
            }
        }

        let scoreColor = '#999';
        let scoreIcon = '';
        if (score >= 90) {
            scoreColor = '#2e7d32';
            scoreIcon = '✅✅ 上吉';
        } else if (score >= 80) {
            scoreColor = '#388e3c';
            scoreIcon = '✅ 中吉';
        } else if (score >= 70) {
            scoreColor = '#f57f17';
            scoreIcon = '✅ 小吉';
        }

        const li = document.createElement('li');
        li.className = 'date-item';
        li.style.display = '';
        li.style.opacity = '1';
        li.dataset.date = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        li.dataset.score = score;
        li.dataset.hour = hourName;
        li.dataset.doushouScore = modules?.doushou?.score || 0;
        li.dataset.doushouKeti = modules?.doushou?.keti || '';
        li.dataset.daliurenScore = modules?.daliuren?.score || 0;
        li.dataset.yanqinScore = modules?.yanqin?.score || 0;
        li.dataset.doushouJixiong = modules?.doushou?.jixiong || '平';
        li.dataset.daliurenJixiong = modules?.daliuren?.jixiong || '平';
        li.dataset.yanqinJixiong = modules?.yanqin?.jixiong || '平';
        li.dataset.daliurenKeti = modules?.daliuren?.keti || '';
        li.dataset.yanqinInfo = modules?.yanqin?.info || '';
        if (dateData.patterns && dateData.patterns.length > 0) {
            li.dataset.patterns = JSON.stringify(dateData.patterns);
        }
        if (dateData.daliuren_detail) {
            li.dataset.daliurenDetail = JSON.stringify(dateData.daliuren_detail);
        }
        li.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 16px; font-weight: bold; color: #333;">
                        ${index + 1}. ${year}年 ${String(month).padStart(2, '0')}月 ${String(day).padStart(2, '0')}日 ${hourName}时
                    </div>
                    <div style="font-size: 12px; color: #666; margin-top: 5px;">
                        ${weekDay} 农历：${lunarText}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 18px; font-weight: bold; color: ${scoreColor};">
                        ${score}分 ${scoreIcon}
                    </div>
                    <div style="font-size: 11px; color: #999; margin-top: 3px;">
                        龙${modules?.longyun?.score || '--'} 山${modules?.zuoshan?.score || '--'} 斗${modules?.doushou?.score || '--'} 六${modules?.daliuren?.score || '--'}
                    </div>
                </div>
            </div>
        `;

        li.addEventListener('click', function() {
            document.querySelectorAll('.date-item').forEach(item => item.classList.remove('selected'));
            this.classList.add('selected');
            const scoreData = {
                doushouScore: parseInt(this.dataset.doushouScore) || 0,
                daliurenScore: parseInt(this.dataset.daliurenScore) || 0,
                yanqinScore: parseInt(this.dataset.yanqinScore) || 0,
                doushouJixiong: this.dataset.doushouJixiong || '平',
                daliurenJixiong: this.dataset.daliurenJixiong || '平',
                yanqinJixiong: this.dataset.yanqinJixiong || '平',
                daliurenKeti: this.dataset.daliurenKeti || '--',
                yanqinInfo: this.dataset.yanqinInfo || '--',
                patterns: this.dataset.patterns ? JSON.parse(this.dataset.patterns) : [],
                daliuren_detail: this.dataset.daliurenDetail ? JSON.parse(this.dataset.daliurenDetail) : null,
                luma_guiren_info: this.dataset.lumaGuirenInfo ? JSON.parse(this.dataset.lumaGuirenInfo) : null
            };
            calculateDate(this.dataset.date, this.dataset.hour, scoreData);
        });

        dateListEl.appendChild(li);
    });
}

// ==================== 生成吉期列表（完整遍历版） ====================
async function generateJiriList(startDate, endDate, count) {
    const dateListEl = document.getElementById('dateList');
    if (!dateListEl) return;

    dateListEl.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">正在遍历所有日期和时辰，请稍候...</div>';

    const zuoshanSelectDisplay = document.getElementById('zuoshanSelectDisplay');
    const currentMountain = zuoshanSelectDisplay ? (zuoshanSelectDisplay.dataset.value || null) : null;

    console.log('📌 generateJiriList - 坐山:', currentMountain);

    if (!currentMountain) {
        alert('请先选择坐山！');
        return;
    }

    const formatDate = (date) => {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    };

    const startStr = formatDate(startDate);
    const endStr = formatDate(endDate);

    console.log('📌 完整日期范围分析:', startStr, '至', endStr);

    const daliurenScoreSelect = document.getElementById('daliurenScoreSelect');
    const minDaliurenScore = daliurenScoreSelect ? parseInt(daliurenScoreSelect.value) || 70 : 70;

    console.log('📌 评分要求 - 大六壬:', minDaliurenScore);
    console.log('📌 筛选规则: 1.大六壬优先 2.斗首不凶即可 3.演禽必须为吉');

    try {
        const selectedMubiao = getSelectedMubiao();
        console.log('📌 用户选择的目标:', selectedMubiao);

        const API_TIMEOUT = 30000;
        let apiResult = null;
        let apiCompleted = false;

        const fetchPromise = fetchApi(`${API_BASE_URL}/api/doushou/full_range_analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mountain: currentMountain,
                start_date: startStr,
                end_date: endStr,
                min_daliuren_score: minDaliurenScore,
                max_results: count || 10,
                mubiao: selectedMubiao,
                _timestamp: Date.now()
            }),
            timeout: 600000,
            onDownloadProgress: (progressEvent) => {
                console.log('下载进度:', progressEvent);
                if (progressEvent.percent) {
                    updateProgress(Math.min(95, progressEvent.percent));
                }
            }
        });

        const timeoutPromise = new Promise((resolve) => {
            setTimeout(() => {
                if (!apiCompleted) {
                    console.warn('⚠️ API请求超时(30秒)，使用兜底机制');
                    resolve({ timeout: true, success: false, error: '请求超时，请尝试缩小日期范围' });
                }
            }, API_TIMEOUT);
        });

        try {
            apiResult = await Promise.race([fetchPromise, timeoutPromise]);
            apiCompleted = true;
        } catch (apiError) {
            apiCompleted = true;
            apiResult = { success: false, error: apiError.message };
        }

        if (progressInterval) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
        updateProgress(100);

        if (apiResult && apiResult.timeout) {
            console.warn('⚠️ API请求超时，直接显示超时信息');
            dateListEl.innerHTML = `<div style="padding: 20px; text-align: center; color: #e65100;">
                <div style="font-weight: bold; margin-bottom: 10px;">⚠️ 请求超时</div>
                <div style="font-size: 12px; color: #666;">服务器处理时间过长，请尝试：<br>1. 缩小日期范围<br>2. 减少结果数量<br>3. 降低大六壬评分阈值</div>
            </div>`;
            hideProgress();
            return;
        }

        const result = apiResult;
        console.log('📌 完整日期范围分析结果:', result);

        if (!result.success) {
            throw new Error(result.error || '分析失败');
        }

        dateListEl.innerHTML = '';
        const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
        let topResults = result.results || [];

        topResults.sort((a, b) => {
            const scoreA = parseFloat(a.total_score) || 0;
            const scoreB = parseFloat(b.total_score) || 0;
            return scoreB - scoreA;
        });

        console.log(`📌 共遍历 ${result.total_days} 天，找到 ${result.total_candidates} 个符合条件的日课`);

        topResults.forEach((dateData, index) => {
            const { date, shichen, sizhu, doushou_score, doushou_keti, daliuren_score, daliuren_keti, yanqin_score, total_score, yanqin_info, patterns, duanyu, mubiao_bonus, matched_mubiao } = dateData;

            let lunarText = '--';
            const [year, month, day] = date.split('-').map(Number);
            if (typeof LunarCalendarExt !== 'undefined') {
                const lunarDate = LunarCalendarExt.solarToLunar(year, month, day);
                if (lunarDate) {
                    lunarText = LunarCalendarExt.formatLunarDate(lunarDate);
                }
            }

            const weekDay = weekDays[new Date(date).getDay()];
            const dateDisplay = `${year}年 ${String(month).padStart(2, '0')}月 ${String(day).padStart(2, '0')}日`;

            const doushouJixiong = doushou_score >= 70 ? '吉' : (doushou_score >= 50 ? '平' : '凶');
            const daliurenJixiong = daliuren_score >= 70 ? '吉' : (daliuren_score >= 50 ? '平' : '凶');
            const yanqinJixiong = yanqin_score >= 85 ? '吉' : (yanqin_score >= 70 ? '平' : '凶');

            const jiCount = (doushouJixiong === '吉' ? 1 : 0) + (daliurenJixiong === '吉' ? 1 : 0) + (yanqinJixiong === '吉' ? 1 : 0);
            const xiongCount = (doushouJixiong === '凶' ? 1 : 0) + (daliurenJixiong === '凶' ? 1 : 0) + (yanqinJixiong === '凶' ? 1 : 0);

            let scoreColor = '#999';
            let scoreIcon = '';
            let jixiongLabel = '';

            if (xiongCount >= 2) {
                scoreColor = '#c62828';
                scoreIcon = '❌';
                jixiongLabel = '凶课';
            } else if (jiCount >= 2) {
                scoreColor = '#2e7d32';
                scoreIcon = '✅✅';
                jixiongLabel = '吉课';
            } else if (jiCount === 1 && xiongCount === 0) {
                scoreColor = '#388e3c';
                scoreIcon = '✅';
                jixiongLabel = '平偏吉';
            } else if (xiongCount === 1 && jiCount === 0) {
                scoreColor = '#f57f17';
                scoreIcon = '⚠️';
                jixiongLabel = '平偏凶';
            } else {
                scoreColor = '#757575';
                scoreIcon = '➖';
                jixiongLabel = '平课';
            }

            let mubiaoHtml = '';
            if (matched_mubiao && matched_mubiao.length > 0) {
                mubiaoHtml = `<div style="font-size: 10px; color: #e65100; margin-top: 2px; font-weight: bold;">🎯 匹配: ${matched_mubiao.join(', ')} +${mubiao_bonus}分</div>`;
            }

            let daliurenDetailHtml = '';
            if (dateData.luma_guiren_info) {
                const lgi = dateData.luma_guiren_info;
                const qualifiedStatus = lgi.is_qualified ? '✅合格' : '❌不合格';
                const pillarDetails = [];
                if (lgi.nian_qualified) pillarDetails.push('年柱✅');
                else pillarDetails.push('年柱❌');
                if (lgi.yue_qualified) pillarDetails.push('月柱✅');
                else pillarDetails.push('月柱❌');
                if (lgi.ri_qualified) pillarDetails.push('日柱✅');
                else pillarDetails.push('日柱❌');
                if (lgi.shi_qualified) pillarDetails.push('时柱✅');
                else pillarDetails.push('时柱❌');
                const sanchuanInfo = lgi.sanchuan_luma_count > 0 ? `, 三传禄马贵人${lgi.sanchuan_luma_count}个` : ', 三传禄马贵人0个';
                daliurenDetailHtml = `
                    <div style="font-size: 9px; color: #666; margin-top: 3px; border-top: 1px dashed #ccc; padding-top: 3px;">
                        六壬详情: ${qualifiedStatus} | 合格数${lgi.qualified_count || 0}/4 | ${pillarDetails.join(' | ')}${sanchuanInfo}
                    </div>
                `;
            }

            const li = document.createElement('li');
            li.className = 'date-item';
            li.dataset.date = date;
            li.dataset.score = total_score;
            li.dataset.hour = shichen;
            li.dataset.doushouScore = doushou_score;
            li.dataset.doushouKeti = doushou_keti || '';
            li.dataset.daliurenScore = daliuren_score;
            li.dataset.yanqinScore = yanqin_score;
            li.dataset.doushouJixiong = doushouJixiong;
            li.dataset.daliurenJixiong = daliurenJixiong;
            li.dataset.yanqinJixiong = yanqinJixiong;
            li.dataset.daliurenKeti = daliuren_keti || '';
            li.dataset.yanqinInfo = yanqin_info || '';
            if (dateData.patterns && dateData.patterns.length > 0) {
                li.dataset.patterns = JSON.stringify(dateData.patterns);
            }
            if (dateData.daliuren_detail) {
                li.dataset.daliurenDetail = JSON.stringify(dateData.daliuren_detail);
            }
            if (dateData.luma_guiren_info) {
                li.dataset.lumaGuirenInfo = JSON.stringify(dateData.luma_guiren_info);
            }
            li.innerHTML = `
                <div>${dateDisplay} ${shichen}时</div>
                <div style="font-size: 12px; color: #666;">${weekDay} 农历：${lunarText || '--'}</div>
                <div style="font-size: 11px; color: #888; margin-top: 3px;">
                    ${sizhu.年柱} ${sizhu.月柱} ${sizhu.日柱} ${sizhu.时柱}
                </div>
                <div style="font-size: 11px; margin-top: 5px; padding: 5px; background: #f5f5f5; border-radius: 4px;">
                    <div style="color: ${scoreColor}; font-weight: bold;">${jixiongLabel} ${scoreIcon} 综合${Math.round(total_score)}分</div>
                    <div style="display: flex; justify-content: space-between; margin-top: 3px; font-size: 10px;">
                        <span style="color: ${doushouJixiong === '吉' ? '#2e7d32' : (doushouJixiong === '凶' ? '#c62828' : '#757575')};">斗首:${doushou_score}分(${doushouJixiong})</span>
                        <span style="color: ${daliurenJixiong === '吉' ? '#2e7d32' : (daliurenJixiong === '凶' ? '#c62828' : '#757575')};">六壬:${daliuren_score}分(${daliurenJixiong})</span>
                        <span style="color: ${yanqinJixiong === '吉' ? '#2e7d32' : (yanqinJixiong === '凶' ? '#c62828' : '#757575')};">演禽:${yanqin_score}分(${yanqinJixiong})</span>
                    </div>
                    ${doushou_keti ? `<div style="font-size: 10px; color: #666; margin-top: 2px;">课体：${doushou_keti}</div>` : ''}
                    ${daliuren_keti ? `<div style="font-size: 10px; color: #1565c1; margin-top: 2px;">六壬：${daliuren_keti}</div>` : ''}
                    ${mubiaoHtml}
                    ${daliurenDetailHtml}
                    ${yanqin_info ? `<div style="font-size: 10px; color: #666; margin-top: 2px;">演禽：${yanqin_info}</div>` : ''}
                </div>
            `;

            li.addEventListener('click', function() {
                document.querySelectorAll('.date-item').forEach(item => item.classList.remove('selected'));
                this.classList.add('selected');
                const scoreData = {
                    doushouScore: parseInt(this.dataset.doushouScore) || 0,
                    daliurenScore: parseInt(this.dataset.daliurenScore) || 0,
                    yanqinScore: parseInt(this.dataset.yanqinScore) || 0,
                    doushouJixiong: this.dataset.doushouJixiong || '平',
                    daliurenJixiong: this.dataset.daliurenJixiong || '平',
                    yanqinJixiong: this.dataset.yanqinJixiong || '平',
                    daliurenKeti: this.dataset.daliurenKeti || '--',
                    yanqinInfo: this.dataset.yanqinInfo || '--',
                    patterns: this.dataset.patterns ? JSON.parse(this.dataset.patterns) : [],
                    daliuren_detail: this.dataset.daliurenDetail ? JSON.parse(this.dataset.daliurenDetail) : null,
                    luma_guiren_info: this.dataset.lumaGuirenInfo ? JSON.parse(this.dataset.lumaGuirenInfo) : null
                };
                calculateDate(this.dataset.date, this.dataset.hour, scoreData);
            });

            dateListEl.appendChild(li);
        });

        const jiriCountDisplay = document.getElementById('jiriCountDisplay');
        if (jiriCountDisplay) {
            jiriCountDisplay.textContent = `共遍历${result.total_days}天${result.total_days * 12}课，筛选出${result.total_candidates}个吉课`;
        }

        hideProgress();

    } catch (error) {
        console.error('❌ 日期范围分析失败:', error);
        console.error('❌ 错误堆栈:', error.stack);

        if (progressInterval) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
        updateProgress(100);

        const errorMsg = error.message || '未知错误';
        dateListEl.innerHTML = `<div style="padding: 20px; text-align: center; color: #c62828;">
            <div style="font-weight: bold; margin-bottom: 10px;">❌ 分析失败</div>
            <div style="font-size: 12px; color: #666;">错误信息: ${errorMsg}</div>
            <div style="font-size: 11px; color: #999; margin-top: 5px;">请检查浏览器控制台获取详细错误信息</div>
        </div>`;

        alert('日期分析失败: ' + errorMsg + '\n\n请检查浏览器控制台(F12)获取详细错误信息');
        hideProgress();
    }
}

// ==================== 初始化函数 ====================
function initDateList() {
    document.querySelectorAll('.date-item').forEach(item => {
        item.addEventListener('click', function() {
            document.querySelectorAll('.date-item').forEach(i => i.classList.remove('selected'));
            this.classList.add('selected');
            calculateDate(this.dataset.date);
        });
    });
}

function initDefaultDates() {
    const today = new Date();
    const startYearEl = document.getElementById('startYear');
    const startMonthEl = document.getElementById('startMonth');
    const startDayEl = document.getElementById('startDay');

    if (startYearEl) startYearEl.value = today.getFullYear();
    if (startMonthEl) startMonthEl.value = today.getMonth() + 1;
    if (startDayEl) startDayEl.value = today.getDate();

    autoCalculateEndDate();
}

function autoCalculateEndDate() {
    const startYearEl = document.getElementById('startYear');
    const startMonthEl = document.getElementById('startMonth');
    const startDayEl = document.getElementById('startDay');

    if (!startYearEl || !startMonthEl || !startDayEl) return;

    const startYear = parseInt(startYearEl.value);
    const startMonth = parseInt(startMonthEl.value);
    const startDay = parseInt(startDayEl.value);

    const endYearEl = document.getElementById('endYear');
    const endMonthEl = document.getElementById('endMonth');
    const endDayEl = document.getElementById('endDay');

    if (!startYear || !startMonth || !startDay) {
        if (endYearEl) endYearEl.value = '';
        if (endMonthEl) endMonthEl.value = '';
        if (endDayEl) endDayEl.value = '';
        return;
    }

    let endYear = startYear + 3;
    let endMonth = startMonth;
    let endDay = startDay;

    if (startMonth === 2 && startDay === 29) {
        if (!((endYear % 4 === 0 && endYear % 100 !== 0) || (endYear % 400 === 0))) {
            endDay = 28;
        }
    }

    if (endYearEl) endYearEl.value = endYear;
    if (endMonthEl) endMonthEl.value = endMonth;
    if (endDayEl) endDayEl.value = endDay;
}

function initNianmingSelects() {
    const nanNianmingSelect = document.getElementById('nanNianmingSelect');
    const nvNianmingSelect = document.getElementById('nvNianmingSelect');

    if (!nanNianmingSelect || !nvNianmingSelect) return;

    const nianmingOptions = [
        '甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳', '庚午', '辛未', '壬申', '癸酉',
        '甲戌', '乙亥', '丙子', '丁丑', '戊寅', '己卯', '庚辰', '辛巳', '壬午', '癸未',
        '甲申', '乙酉', '丙戌', '丁亥', '戊子', '己丑', '庚寅', '辛卯', '壬辰', '癸巳',
        '甲午', '乙未', '丙申', '丁酉', '戊戌', '己亥', '庚子', '辛丑', '壬寅', '癸卯',
        '甲辰', '乙巳', '丙午', '丁未', '戊申', '己酉', '庚戌', '辛亥', '壬子', '癸丑',
        '甲寅', '乙卯', '丙辰', '丁巳', '戊午', '己未', '庚申', '辛酉', '壬戌', '癸亥'
    ];

    nianmingOptions.forEach(item => {
        const option = document.createElement('option');
        option.value = item;
        option.textContent = item;
        nanNianmingSelect.appendChild(option);
    });

    nianmingOptions.forEach(item => {
        const option = document.createElement('option');
        option.value = item;
        option.textContent = item;
        nvNianmingSelect.appendChild(option);
    });
}

function onZetiriTypeChange() {
    const zetiriTypeSelect = document.getElementById('zetiriTypeSelect');
    const typeValue = zetiriTypeSelect ? zetiriTypeSelect.value : '';

    console.log('📌 onZetiriTypeChange 被调用，当前类型:', typeValue);

    const zuoshanRow = document.getElementById('zuoshanRow');
    const nianmingRow = document.getElementById('nianmingRow');
    const mubiaoRow = document.getElementById('mubiaoRow');
    const zuoshanSelectDisplay = document.getElementById('zuoshanSelectDisplay');
    const btnStartZeri = document.getElementById('btnStartZeri');
    const lailongLabel = document.getElementById('lailongLabel');
    const lailongSelect = document.getElementById('lailongSelect');

    const fuzhuRow = document.getElementById('fuzhuRow');
    const fuzhuBirthRow = document.getElementById('fuzhuBirthRow');
    const fuzhuLocationRow = document.getElementById('fuzhuLocationRow');

    console.log('📌 zuoshanSelectDisplay 元素:', zuoshanSelectDisplay);
    console.log('📌 zuoshanSelectDisplay.style.pointerEvents:', zuoshanSelectDisplay?.style.pointerEvents);

    if (typeValue === '') {
        if (btnStartZeri) {
            btnStartZeri.disabled = true;
            btnStartZeri.classList.remove('enabled');
        }
    } else {
        if (btnStartZeri) {
            btnStartZeri.disabled = false;
            btnStartZeri.classList.add('enabled');
            setTimeout(() => {
                btnStartZeri.classList.remove('enabled');
            }, 500);
        }
    }

    if (typeValue === '天时') {
        if (fuzhuRow) fuzhuRow.style.display = 'none';
        if (fuzhuBirthRow) fuzhuBirthRow.style.display = 'none';
        if (fuzhuLocationRow) fuzhuLocationRow.style.display = 'none';
        if (zuoshanRow) zuoshanRow.style.display = 'none';
        if (lailongSelect) {
            lailongSelect.setAttribute('disabled', 'disabled');
        }
        if (lailongLabel) lailongLabel.textContent = '来龙：';
        if (nianmingRow) nianmingRow.style.display = 'none';
        if (mubiaoRow) mubiaoRow.style.display = 'none';
    } else {
        if (fuzhuRow) fuzhuRow.style.display = 'flex';
        if (fuzhuBirthRow) fuzhuBirthRow.style.display = 'flex';
        if (fuzhuLocationRow) fuzhuLocationRow.style.display = 'flex';
        initFuzhuBirthYear();
        initFuzhuBirthDay();
    }

    if (typeValue === '婚嫁') {
        if (zuoshanRow) zuoshanRow.style.display = 'none';
        if (zuoshanSelectDisplay) {
            zuoshanSelectDisplay.style.pointerEvents = 'none';
            zuoshanSelectDisplay.style.opacity = '0.5';
        }
        if (lailongSelect) {
            lailongSelect.removeAttribute('disabled');
        }
        if (lailongLabel) lailongLabel.textContent = '来龙：';
        initLailongDropdown();
        if (nianmingRow) nianmingRow.style.display = 'flex';
        if (mubiaoRow) mubiaoRow.style.display = 'none';
    } else if (typeValue === '立碑' || typeValue === '安葬') {
        console.log('📌 进入立碑/安葬分支，启用坐山选择');
        if (zuoshanRow) zuoshanRow.style.display = 'flex';
        if (zuoshanSelectDisplay) {
            console.log('📌 设置 pointerEvents = auto');
            zuoshanSelectDisplay.style.pointerEvents = 'auto';
            zuoshanSelectDisplay.style.opacity = '1';
            console.log('📌 设置后 pointerEvents:', zuoshanSelectDisplay.style.pointerEvents);
        }
        if (lailongSelect) {
            lailongSelect.removeAttribute('disabled');
        }
        if (lailongLabel) lailongLabel.textContent = '来龙：';
        initLailongDropdown();
        if (mubiaoRow) mubiaoRow.style.display = 'flex';
        if (nianmingRow) nianmingRow.style.display = 'none';
    } else if (typeValue === '开业') {
        if (zuoshanRow) zuoshanRow.style.display = 'flex';
        if (zuoshanSelectDisplay) {
            zuoshanSelectDisplay.style.pointerEvents = 'auto';
            zuoshanSelectDisplay.style.opacity = '1';
        }
        if (lailongSelect) {
            lailongSelect.removeAttribute('disabled');
        }
        if (lailongLabel) lailongLabel.textContent = '福主属相：';
        initFuzhuShuxiangDropdown();
        if (nianmingRow) nianmingRow.style.display = 'none';
        if (mubiaoRow) mubiaoRow.style.display = 'none';
    } else {
        if (zuoshanRow) zuoshanRow.style.display = 'flex';
        if (zuoshanSelectDisplay) {
            zuoshanSelectDisplay.style.pointerEvents = 'auto';
            zuoshanSelectDisplay.style.opacity = '1';
        }
        if (lailongSelect) {
            lailongSelect.setAttribute('disabled', 'disabled');
        }
        if (lailongLabel) lailongLabel.textContent = '来龙：';
        if (nianmingRow) nianmingRow.style.display = 'none';
        if (mubiaoRow) mubiaoRow.style.display = 'none';
    }
}

function getSelectedMubiao() {
    const mubiaoList = [];
    const mubiaoIds = ['mubiaoQiuguan', 'mubiaoQiucai', 'mubiaoQiufugui', 'mubiaoQiuzi', 'mubiaoQiuwenxue', 'mubiaoQiuhunyin'];
    mubiaoIds.forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox && checkbox.checked) {
            mubiaoList.push(checkbox.value);
        }
    });
    return mubiaoList;
}

function initFuzhuShuxiangDropdown() {
    const lailongSelect = document.getElementById('lailongSelect');
    if (!lailongSelect) return;

    const shengxiao = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪'];

    lailongSelect.innerHTML = '<option value="">请选择福主属相</option>';

    shengxiao.forEach(sx => {
        const option = document.createElement('option');
        option.value = sx;
        option.textContent = sx + '相';
        lailongSelect.appendChild(option);
    });
}

function initFuzhuBirthYear() {
    const fuzhuBirthYear = document.getElementById('fuzhuBirthYear');
    if (!fuzhuBirthYear) return;

    fuzhuBirthYear.innerHTML = '<option value="">年</option>';

    const currentYear = new Date().getFullYear();
    for (let year = currentYear; year >= currentYear - 100; year--) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year + '年';
        fuzhuBirthYear.appendChild(option);
    }
}

function initFuzhuBirthDay() {
    const fuzhuBirthYear = document.getElementById('fuzhuBirthYear');
    const fuzhuBirthMonth = document.getElementById('fuzhuBirthMonth');
    const fuzhuBirthDay = document.getElementById('fuzhuBirthDay');
    if (!fuzhuBirthDay) return;

    const year = parseInt(fuzhuBirthYear ? fuzhuBirthYear.value : '');
    const month = parseInt(fuzhuBirthMonth ? fuzhuBirthMonth.value : '');
    const daysInMonth = getDaysInMonth(year, month);

    fuzhuBirthDay.innerHTML = '<option value="">日</option>';

    for (let day = 1; day <= daysInMonth; day++) {
        const option = document.createElement('option');
        option.value = day;
        option.textContent = day + '日';
        fuzhuBirthDay.appendChild(option);
    }
}

function getDaysInMonth(year, month) {
    if (!year || !month) return 30;
    const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    if (month === 2 && ((year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0))) {
        return 29;
    }
    return daysInMonth[month - 1] || 30;
}

// ==================== 弹窗/UI 功能 ====================
function openScoreFilter() {
    const modal = document.getElementById('scoreFilterModal');
    modal.classList.add('show');
}

function closeScoreFilter() {
    const modal = document.getElementById('scoreFilterModal');
    modal.classList.remove('show');
}

function applyScoreFilter() {
    const threshold = parseInt(document.getElementById('scoreThreshold').value);
    const filterRange = document.querySelector('input[name="filterRange"]:checked').value;

    if (isNaN(threshold) || threshold < 0 || threshold > 100) {
        alert('请输入有效的分值（0-100）！');
        return;
    }

    const dateItems = document.querySelectorAll('.date-item');
    let filteredCount = 0;

    dateItems.forEach(item => {
        const score = parseInt(item.dataset.score || '0');
        if (score >= threshold) {
            item.style.display = '';
            item.style.opacity = '1';
            filteredCount++;
        } else {
            item.style.display = 'none';
            item.style.opacity = '0.5';
        }
    });

    closeScoreFilter();
}

function openKetiDetail(ketiName, score) {
    const modal = document.getElementById('ketiDetailModal');
    const contentDiv = document.getElementById('ketiDetailContent');

    contentDiv.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <p>正在加载课体信息...</p>
        </div>
    `;

    modal.classList.add('show');

    setTimeout(() => {
        loadKetiDetail(ketiName, score);
    }, 500);
}

function loadKetiDetail(ketiName, score) {
    const contentDiv = document.getElementById('ketiDetailContent');

    const ketiData = {
        '元辰得位': {
            desc: '元辰星得位，主富贵荣华，家宅兴旺',
            params: { '五行': '生入', '吉凶': '大吉', '应期': '速发' },
            detail: '元辰为生我之星，得位则力量倍增。主子孙昌盛，财源广进，官贵显达。最利于安葬、立碑、婚嫁、开业等重大事项。'
        },
        '元辰旺相': {
            desc: '元辰星旺相，主家业兴隆，人丁兴旺',
            params: { '五行': '比和', '吉凶': '上吉', '应期': '中期' },
            detail: '元辰旺相，生气勃勃。主家庭和睦，事业顺利，健康长寿。适宜各类吉祥事务。'
        },
        '廉贞守值': {
            desc: '廉贞星守值，主平安顺利，无灾无祸',
            params: { '五行': '我生', '吉凶': '平', '应期': '平稳' },
            detail: '廉贞为我生之星（子孙），守值则百事顺遂。虽无大发，但求平安。适合日常事务。'
        },
        '武财临山': {
            desc: '武财星临山，主子孙兴旺，财源滚滚',
            params: { '五行': '我克', '吉凶': '吉', '应期': '晚发' },
            detail: '武财为我克之星（妻财），临山则后代昌盛。主子孙贤孝，财源稳定。利于长远规划。'
        },
        '破鬼当值': {
            desc: '破鬼星当值，主破财损丁，需谨慎',
            params: { '五行': '克出', '吉凶': '凶', '应期': '速应' },
            detail: '破鬼为我克之星，当值则耗泄元气。主破财、疾病、口舌。不宜重大事项。'
        },
        '贪官克山': {
            desc: '贪官星克山，主灾祸疾病，大凶',
            params: { '五行': '克入', '吉凶': '大凶', '应期': '即应' },
            detail: '贪官为克我之星，克山则灾祸临头。主重病、破败、伤亡。切勿使用。'
        }
    };

    const data = ketiData[ketiName] || {
        desc: `${ketiName}，斗首课体之一`,
        params: { '五行': '未知', '吉凶': score >= 70 ? '吉' : '凶', '应期': '视情况而定' },
        detail: `此课体得分为${score}分。${score >= 70 ? '为吉课，可以使用。' : '为凶课，不宜使用。'}`
    };

    contentDiv.innerHTML = `
        <div class="keti-details">
            <div class="keti-header">
                <div class="keti-name">${ketiName || '未知课体'}</div>
                <div class="keti-score">评分：${score || '--'}分</div>
            </div>

            <div class="keti-info-section">
                <div class="keti-info-title">📖 课体特征</div>
                <div class="keti-info-content">${data.desc}</div>
            </div>

            <div class="keti-info-section">
                <div class="keti-info-title">⚙️ 相关参数</div>
                <div class="keti-params">
                    ${Object.entries(data.params).map(([key, value]) => `
                        <div class="keti-param-item">
                            <div class="keti-param-label">${key}</div>
                            <div class="keti-param-value">${value}</div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="keti-info-section">
                <div class="keti-info-title">💡 详细解读</div>
                <div class="keti-description">${data.detail}</div>
            </div>
        </div>
    `;
}

function closeKetiDetail() {
    const modal = document.getElementById('ketiDetailModal');
    modal.classList.remove('show');
}

// ==================== 日期详情弹窗 ====================
function openDateDetail(dateInfo) {
    const modal = document.getElementById('dateDetailModal');
    const contentDiv = document.getElementById('dateDetailContent');

    const doushouKeti = document.getElementById('doushouKeti')?.textContent || '元辰旺相';
    const doushouScoreEl = document.getElementById('doushouScore');
    const doushouScore = doushouScoreEl ? parseInt(doushouScoreEl.textContent) : 90;

    const daliurenKeti = document.getElementById('daliurenKeti')?.textContent || '重审课';
    const daliurenScoreEl = document.getElementById('daliurenScore');
    const daliurenScore = daliurenScoreEl ? parseInt(daliurenScoreEl.textContent) : 70;

    let sixPhaseWarningHTML = '';
    const dayPillarEl = document.getElementById('dayPillar');
    const currentMountainEl = document.getElementById('zuoshanSelectDisplay');
    if (dayPillarEl && currentMountainEl && currentMountainEl.dataset.value) {
        const dayGanZhi = dayPillarEl.textContent;
        const dayGan = dayGanZhi.charAt(0);
        const dayZhi = dayGanZhi.charAt(1);
        const mountain = currentMountainEl.dataset.value;

        if (window.judgeSixPhaseLuck) {
            try {
                const sixPhaseResult = window.judgeSixPhaseLuck(mountain, dayGan, dayZhi);
                if (sixPhaseResult.luck === '大凶') {
                    sixPhaseWarningHTML = `
                        <div class="sixphase-warning" style="
                            background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
                            border: 3px solid #c62828;
                            border-radius: 10px;
                            padding: 20px;
                            margin-bottom: 20px;
                            box-shadow: 0 4px 15px rgba(198, 40, 40, 0.3);
                        ">
                            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                <span style="font-size: 32px; margin-right: 15px;">⚠️</span>
                                <div>
                                    <div style="font-size: 18px; font-weight: bold; color: #c62828; margin-bottom: 5px;">
                                        六相六替大凶警告
                                    </div>
                                    <div style="font-size: 14px; color: #666;">
                                        此日课六相六替为大凶，请勿使用！
                                    </div>
                                </div>
                            </div>
                            <div style="background: white; border-left: 4px solid #c62828; padding: 15px; border-radius: 5px;">
                                <div style="font-size: 15px; line-height: 1.8; color: #333;">
                                    <strong>坐山：</strong>${mountain}山<br>
                                    <strong>日干支：</strong>${dayGan}${dayZhi}<br>
                                    <strong>化气五行：</strong>${sixPhaseResult.huaQiElement}<br>
                                    <strong>十二长生：</strong>${sixPhaseResult.lifeStage || '未知'}<br>
                                    <strong>断语：</strong><span style="color: #c62828; font-weight: bold;">${sixPhaseResult.description}</span>
                                </div>
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('六相六替检查失败:', error);
            }
        }
    }

    let contentHTML = '';

    if (sixPhaseWarningHTML) {
        contentHTML += sixPhaseWarningHTML;
    } else {
        contentHTML += `
            <div style="padding: 20px; text-align: center;">
                <h3 style="color: #4caf50; margin-bottom: 10px;">✅ 六相六替无大凶</h3>
                <p style="color: #666;">此日课六相六替无大凶，可结合其他因素综合判断。</p>
            </div>
        `;
    }

    contentDiv.innerHTML = contentHTML;
    modal.classList.add('show');
}

function closeDateDetail() {
    const modal = document.getElementById('dateDetailModal');
    if (modal) modal.classList.remove('show');
}

// ==================== AI 模块拖动和缩放功能 ====================
function initDragAndScale() {
    const windowEl = document.getElementById('dateDetailWindow');
    const headerEl = document.getElementById('dateDetailHeader');
    const dragHintEl = document.getElementById('dragHint');

    if (!windowEl || !headerEl) return;

    let isDragging = false;
    let startX, startY, initialX, initialY;
    let currentX = 0, currentY = 0;

    let currentScale = 1;
    const minScale = 0.5;
    const maxScale = 1.0;

    headerEl.addEventListener('mousedown', function(e) {
        if (e.target.tagName === 'BUTTON') return;
        isDragging = true;
        windowEl.classList.add('dragging');
        startX = e.clientX;
        startY = e.clientY;
        const style = window.getComputedStyle(windowEl);
        const matrix = new DOMMatrix(style.transform);
        currentX = matrix.m41;
        currentY = matrix.m42;
        e.preventDefault();
    });

    headerEl.addEventListener('touchstart', function(e) {
        if (e.target.tagName === 'BUTTON') return;
        isDragging = true;
        windowEl.classList.add('dragging');
        const touch = e.touches[0];
        startX = touch.clientX;
        startY = touch.clientY;
        const style = window.getComputedStyle(windowEl);
        const matrix = new DOMMatrix(style.transform);
        currentX = matrix.m41;
        currentY = matrix.m42;
        e.preventDefault();
    }, { passive: false });

    document.addEventListener('mousemove', function(e) {
        if (!isDragging) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        const newX = currentX + dx;
        const newY = currentY + dy;
        const rect = windowEl.getBoundingClientRect();
        const maxX = window.innerWidth - rect.width * currentScale;
        const maxY = window.innerHeight - rect.height * currentScale;
        const boundedX = Math.max(-rect.width * currentScale / 2, Math.min(newX, maxX));
        const boundedY = Math.max(-rect.height * currentScale / 2, Math.min(newY, maxY));
        windowEl.style.transform = `translate(${boundedX}px, ${boundedY}px) scale(${currentScale})`;
        e.preventDefault();
    });

    document.addEventListener('touchmove', function(e) {
        if (!isDragging) return;
        const touch = e.touches[0];
        const dx = touch.clientX - startX;
        const dy = touch.clientY - startY;
        const newX = currentX + dx;
        const newY = currentY + dy;
        const rect = windowEl.getBoundingClientRect();
        const maxX = window.innerWidth - rect.width * currentScale;
        const maxY = window.innerHeight - rect.height * currentScale;
        const boundedX = Math.max(-rect.width * currentScale / 2, Math.min(newX, maxX));
        const boundedY = Math.max(-rect.height * currentScale / 2, Math.min(newY, maxY));
        windowEl.style.transform = `translate(${boundedX}px, ${boundedY}px) scale(${currentScale})`;
        e.preventDefault();
    }, { passive: false });

    document.addEventListener('mouseup', function() {
        if (isDragging) {
            isDragging = false;
            windowEl.classList.remove('dragging');
        }
    });

    document.addEventListener('touchend', function() {
        if (isDragging) {
            isDragging = false;
            windowEl.classList.remove('dragging');
        }
    });

    windowEl.addEventListener('wheel', function(e) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.05 : 0.05;
        const newScale = Math.max(minScale, Math.min(maxScale, currentScale + delta));
        if (newScale !== currentScale) {
            currentScale = newScale;
            windowEl.classList.add('scaling');
            const style = window.getComputedStyle(windowEl);
            const matrix = new DOMMatrix(style.transform);
            const translateX = matrix.m41;
            const translateY = matrix.m42;
            windowEl.style.transform = `translate(${translateX}px, ${translateY}px) scale(${currentScale})`;
            showDragHint(`缩放：${Math.round(currentScale * 100)}%`);
            setTimeout(() => {
                windowEl.classList.remove('scaling');
            }, 100);
        }
    }, { passive: false });

    let initialPinchDistance = null;

    headerEl.addEventListener('touchstart', function(e) {
        if (e.touches.length === 2) {
            initialPinchDistance = getPinchDistance(e.touches);
        }
    }, { passive: false });

    document.addEventListener('touchmove', function(e) {
        if (e.touches.length === 2 && initialPinchDistance !== null) {
            e.preventDefault();
            const currentDistance = getPinchDistance(e.touches);
            const delta = (currentDistance - initialPinchDistance) / 100;
            const newScale = Math.max(minScale, Math.min(maxScale, currentScale + delta));
            if (newScale !== currentScale) {
                currentScale = newScale;
                windowEl.classList.add('scaling');
                const style = window.getComputedStyle(windowEl);
                const matrix = new DOMMatrix(style.transform);
                const translateX = matrix.m41;
                const translateY = matrix.m42;
                windowEl.style.transform = `translate(${translateX}px, ${translateY}px) scale(${currentScale})`;
                showDragHint(`缩放：${Math.round(currentScale * 100)}%`);
                initialPinchDistance = currentDistance;
                setTimeout(() => {
                    windowEl.classList.remove('scaling');
                }, 100);
            }
        }
    }, { passive: false });

    document.addEventListener('touchend', function() {
        initialPinchDistance = null;
    });

    function getPinchDistance(touches) {
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    function showDragHint(text) {
        if (dragHintEl) {
            dragHintEl.textContent = text;
            dragHintEl.classList.add('show');
            setTimeout(() => {
                dragHintEl.classList.remove('show');
            }, 1000);
        }
    }
}

// ==================== 自动初始化大六壬排盘 ====================
async function initDaliurenPaiPan() {
    console.log('===== 自动初始化大六壬排盘 =====');

    try {
        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth() + 1;
        const day = now.getDate();
        const hour = now.getHours();

        console.log('当前日期时间:', { year, month, day, hour });

        const sizhuResponse = await fetch(`${API_BASE_URL}/api/sizhu?year=${year}&month=${month}&day=${day}&hour=${hour}`);

        if (sizhuResponse.ok) {
            const sizhuResult = await sizhuResponse.json();
            console.log('四柱API返回:', sizhuResult);

            if (sizhuResult.success && sizhuResult.sizhu) {
                const sz = sizhuResult.sizhu;
                const dayGan = sz.dayGan;
                const dayZhi = sz.dayZhi;

                console.log('日干支:', dayGan, dayZhi);

                const paipanResult = await daliurenPaiPan(year, month, day, hour, dayGan, dayZhi);

                console.log('大六壬排盘结果:', paipanResult);

                if (paipanResult) {
                    console.log('✅ 大六壬排盘初始化成功');
                }
            }
        }
    } catch (error) {
        console.error('自动初始化大六壬排盘失败:', error);
    }
}

function exitApplication() {
    if (confirm('确定要退出应用吗？')) {
        window.close();
        alert('请关闭浏览器窗口以退出应用');
    }
}

// ==================== 全局事件监听 ====================
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.classList.remove('show');
        }
    });
});

const dateDetailModal = document.getElementById('dateDetailModal');
if (dateDetailModal) {
    dateDetailModal.addEventListener('click', function(e) {
        if (e.target === this) {
            closeDateDetail();
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const zhanshiDateInput = document.getElementById('zhanshiDateInput');
    if (zhanshiDateInput) {
        const today = new Date().toISOString().split('T')[0];
        zhanshiDateInput.value = today;
    }
    initZhanshiTime();
    initDragAndScale();
    initNianmingSelects();
    onZetiriTypeChange();
    initDaliurenPaiPan();
});