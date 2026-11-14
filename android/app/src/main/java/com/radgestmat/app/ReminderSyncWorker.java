package com.radgestmat.app;

import android.content.Context;
import androidx.work.*;
import java.util.concurrent.TimeUnit;

public class ReminderSyncWorker extends Worker {
    public ReminderSyncWorker(Context context, WorkerParameters params) { super(context, params); }
    @Override public Result doWork() {
        try { ReminderSync.run(getApplicationContext()); return Result.success(); }
        catch (Exception e) { return Result.retry(); }
    }
    public static void schedule(Context context) {
        Constraints constraints = new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();
        PeriodicWorkRequest work = new PeriodicWorkRequest.Builder(ReminderSyncWorker.class, 15, TimeUnit.MINUTES)
            .setConstraints(constraints).build();
        WorkManager.getInstance(context).enqueueUniquePeriodicWork("reminder-sync", ExistingPeriodicWorkPolicy.KEEP, work);
    }
    public static void refresh(Context context) {
        Constraints constraints = new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();
        WorkManager.getInstance(context).enqueueUniqueWork("reminder-refresh", ExistingWorkPolicy.KEEP,
            new OneTimeWorkRequest.Builder(ReminderSyncWorker.class).setConstraints(constraints).build());
    }
}
