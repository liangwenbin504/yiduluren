/**
 * 简化版四柱计算模块
 * 用于仪度六壬择日系统
 */

const LunarCalendar = {
    // 天干
    TIANGAN: ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'],
    // 地支
    DIZHI: ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'],
    
    // 节气数据（简化版，实际应使用精确数据）
    JIEQI: {
        2026: { '立春': new Date(2026, 1, 4), '雨水': new Date(2026, 1, 19), '惊蛰': new Date(2026, 2, 6), '春分': new Date(2026, 2, 21) },
        2027: { '立春': new Date(2027, 1, 4), '雨水': new Date(2027, 1, 19), '惊蛰': new Date(2027, 2, 6), '春分': new Date(2027, 2, 21) },
        2028: { '立春': new Date(2028, 1, 4), '雨水': new Date(2028, 1, 19), '惊蛰': new Date(2028, 2, 5), '春分': new Date(2028, 2, 20) },
        2029: { '立春': new Date(2029, 1, 3), '雨水': new Date(2029, 1, 18), '惊蛰': new Date(2029, 2, 5), '春分': new Date(2029, 2, 20) }
    },
    
    // 计算年柱
    getYearPillar(year, month, day) {
        // 简化计算：以立春为界
        const liChun = this.getJieqiDate(year, '立春');
        let actualYear = year;
        
        if (liChun && new Date(year, month - 1, day) < liChun) {
            actualYear = year - 1;
        }
        
        // 年干支计算
        const ganIndex = (actualYear - 4) % 10;
        const zhiIndex = (actualYear - 4) % 12;
        
        return {
            gan: this.TIANGAN[ganIndex],
            zhi: this.DIZHI[zhiIndex],
            ganzhi: this.TIANGAN[ganIndex] + this.DIZHI[zhiIndex]
        };
    },
    
    // 计算月柱
    getMonthPillar(year, month, day) {
        // 获取年干
        const yearPillar = this.getYearPillar(year, month, day);
        const yearGanIndex = this.TIANGAN.indexOf(yearPillar.gan);
        
        // 月干支计算（简化版）
        // 月干 = (年干序号 * 2 + 月序号) % 10
        // 月支 = (月序号 + 2) % 12
        let actualMonth = month;
        
        // 简化节气判断
        const jieqiDates = this.JIEQI[year] || {};
        const monthStart = new Date(year, month - 1, 1);
        
        for (const [name, date] of Object.entries(jieqiDates)) {
            if (date.getMonth() === month - 1 && new Date(year, month - 1, day) < date) {
                actualMonth = month - 1 || 12;
                break;
            }
        }
        
        const ganIndex = (yearGanIndex * 2 + actualMonth) % 10;
        const zhiIndex = (actualMonth + 1) % 12;
        
        return {
            gan: this.TIANGAN[ganIndex],
            zhi: this.DIZHI[zhiIndex],
            ganzhi: this.TIANGAN[ganIndex] + this.DIZHI[zhiIndex]
        };
    },
    
    // 计算日柱
    getDayPillar(year, month, day) {
        // 使用基准日期计算
        // 基准：1900年1月1日为甲戌日
        const baseDate = new Date(1900, 0, 1);
        const targetDate = new Date(year, month - 1, day);
        const diffDays = Math.floor((targetDate - baseDate) / (1000 * 60 * 60 * 24));
        
        // 日干支计算
        const ganIndex = (diffDays + 10) % 10;
        const zhiIndex = (diffDays + 10) % 12;
        
        return {
            gan: this.TIANGAN[ganIndex],
            zhi: this.DIZHI[zhiIndex],
            ganzhi: this.TIANGAN[ganIndex] + this.DIZHI[zhiIndex]
        };
    },
    
    // 计算时柱
    getHourPillar(dayGan, hour) {
        // 时辰对应
        const hourZhi = this.getHourZhi(hour);
        const hourZhiIndex = this.DIZHI.indexOf(hourZhi);
        
        // 时干计算
        // 时干 = (日干序号 * 2 + 时支序号) % 10
        const dayGanIndex = this.TIANGAN.indexOf(dayGan);
        const ganIndex = (dayGanIndex * 2 + hourZhiIndex) % 10;
        
        return {
            gan: this.TIANGAN[ganIndex],
            zhi: hourZhi,
            ganzhi: this.TIANGAN[ganIndex] + hourZhi
        };
    },
    
    // 获取时辰地支
    getHourZhi(hour) {
        if (hour >= 23 || hour < 1) return '子';
        if (hour >= 1 && hour < 3) return '丑';
        if (hour >= 3 && hour < 5) return '寅';
        if (hour >= 5 && hour < 7) return '卯';
        if (hour >= 7 && hour < 9) return '辰';
        if (hour >= 9 && hour < 11) return '巳';
        if (hour >= 11 && hour < 13) return '午';
        if (hour >= 13 && hour < 15) return '未';
        if (hour >= 15 && hour < 17) return '申';
        if (hour >= 17 && hour < 19) return '酉';
        if (hour >= 19 && hour < 21) return '戌';
        return '亥';
    },
    
    // 获取节气日期
    getJieqiDate(year, jieqiName) {
        const jieqi = this.JIEQI[year];
        return jieqi ? jieqi[jieqiName] : null;
    },
    
    // 计算四柱
    calculateFourPillars(year, month, day, hour, minute) {
        try {
            // 年柱
            const yearPillar = this.getYearPillar(year, month, day);
            
            // 月柱
            const monthPillar = this.getMonthPillar(year, month, day);
            
            // 日柱
            const dayPillar = this.getDayPillar(year, month, day);
            
            // 时柱
            const hourPillar = this.getHourPillar(dayPillar.gan, hour);
            
            return {
                year: yearPillar.ganzhi,
                month: monthPillar.ganzhi,
                day: dayPillar.ganzhi,
                hour: hourPillar.ganzhi,
                details: {
                    yearGan: yearPillar.gan,
                    yearZhi: yearPillar.zhi,
                    monthGan: monthPillar.gan,
                    monthZhi: monthPillar.zhi,
                    dayGan: dayPillar.gan,
                    dayZhi: dayPillar.zhi,
                    hourGan: hourPillar.gan,
                    hourZhi: hourPillar.zhi
                }
            };
        } catch (error) {
            console.error('四柱计算错误:', error);
            throw error;
        }
    }
};

// 农历扩展模块（简化版）
const LunarCalendarExt = {
    // 农历数据（简化版）
    LUNAR_DATA: {
        2026: { months: [29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30], leap: null },
        2027: { months: [30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29], leap: null },
        2028: { months: [29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30], leap: null },
        2029: { months: [30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29], leap: null }
    },
    
    // 天干地支
    TIANGAN: ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'],
    DIZHI: ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'],
    
    // 农历月份名称
    LUNAR_MONTH_NAMES: ['正', '二', '三', '四', '五', '六', '七', '八', '九', '十', '冬', '腊'],
    LUNAR_DAY_NAMES: ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十',
                      '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
                      '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十'],
    
    // 公历转农历（简化版）
    solarToLunar(year, month, day) {
        // 简化计算，返回基本农历信息
        const lunarMonth = month; // 简化处理
        const lunarDay = day; // 简化处理
        
        return {
            year: year,
            month: lunarMonth,
            day: lunarDay,
            isLeap: false,
            monthName: this.LUNAR_MONTH_NAMES[lunarMonth - 1] + '月',
            dayName: this.LUNAR_DAY_NAMES[lunarDay - 1] || '初一'
        };
    },
    
    // 格式化农历日期
    formatLunarDate(lunarDate) {
        if (!lunarDate) return '';
        return lunarDate.monthName + lunarDate.dayName;
    }
};

console.log('✅ 农历历法模块加载完成');
