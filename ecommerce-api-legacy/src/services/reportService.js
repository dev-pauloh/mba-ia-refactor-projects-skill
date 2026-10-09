const { PAYMENT_STATUS, UNKNOWN_STUDENT } = require('../config/constants');

class ReportService {
    constructor({ courseModel }) {
        this.courseModel = courseModel;
    }

    async financialReport() {
        const rows = await this.courseModel.listEnrollmentPayments();
        const byCourse = new Map();

        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { course: row.title, revenue: 0, students: [] });
            }
            const courseData = byCourse.get(row.course_id);
            if (row.enrollment_id === null) continue; // curso sem matrículas

            if (row.status === PAYMENT_STATUS.PAID) courseData.revenue += row.amount;
            courseData.students.push({
                student: row.student ?? UNKNOWN_STUDENT,
                paid: row.amount ?? 0,
            });
        }

        return [...byCourse.values()];
    }
}

module.exports = { ReportService };
