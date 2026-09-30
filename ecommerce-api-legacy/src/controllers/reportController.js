const { PaymentStatus } = require('../config/constants');

const UNKNOWN_STUDENT = 'Unknown';

class ReportController {
    constructor({ courseModel }) {
        this.courseModel = courseModel;
    }

    async financialReport() {
        const rows = await this.courseModel.findEnrollmentPaymentRows();
        const byCourse = new Map();

        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { course: row.title, revenue: 0, students: [] });
            }
            if (row.enrollment_id === null) continue;

            const courseData = byCourse.get(row.course_id);
            if (row.status === PaymentStatus.PAID) courseData.revenue += row.amount;
            courseData.students.push({
                student: row.student ?? UNKNOWN_STUDENT,
                paid: row.amount ?? 0,
            });
        }

        return [...byCourse.values()];
    }
}

module.exports = ReportController;
